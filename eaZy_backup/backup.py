import datetime
import os

from eaZy_backup.association_list_search import association_list_search
from eaZy_backup.config import BACKUPS_PATH, main_configs
from eaZy_backup.config_object import ConfigConstruct
from eaZy_backup.exceptions.LocalBackupsSavePathNotFound import LocalBackupsSavePathNotFound
from eaZy_backup.exceptions.LocalBackupsSavePathsNotFound import LocalBackupsSavePathsNotFound
from eaZy_backup.log import configure_client_logs
from concurrent.futures import as_completed
import subprocess
import zipfile
import requests
import mimetypes

from eaZy_backup._path import normalize_path, normalize_dir
from eaZy_backup.parallels import make_thread_pool_executor

logger = configure_client_logs()


def backup(_config, time):
    logger.info("Запуск бэкапа: " + _config.dir_name + " Время: " + time)

    if "before_backup_scripts" in _config.files:
        logger.info("Запускаю скрипты перед запуском бэкапа")
        if not launch_scripts(_config.files["before_backup_scripts"], "Скрипт перед запуском бэкапа: "):
            logger.info("Отмена запуска бэкапа. Не все скрипты завершились с кодом 1")

    archive_paths, backup_filenames, archive_paths_to_delete = make_archives(_config)

    upload_backups_to_server = False
    if "UPLOAD_BACKUPS_TO_SERVER" in _config.files["config"]:
        upload_backups_to_server = _config.files["config"]["UPLOAD_BACKUPS_TO_SERVER"]

    if upload_backups_to_server:
        upload_backups(archive_paths, backup_filenames, _config)

    local_backups_save = False
    if "LOCAL_BACKUPS_SAVE" in _config.files["config"]:
        local_backups_save = _config.files["config"]["LOCAL_BACKUPS_SAVE"]
        if local_backups_save:
            if "local_backups_save_path" not in _config.files:
                raise LocalBackupsSavePathNotFound("Не найден файл local_backups_save_path в директории конфигурации")
            else:
                if len(_config.files["local_backups_save_path"]) == 0:
                    raise LocalBackupsSavePathsNotFound(
                        "Файл local_backups_save_path не содержит пути для сохранения бэкапов."
                        " Отключите LOCAL_BACKUPS_SAVE в файле config или заполните файл")
    if local_backups_save:
        logger.info("Сохраняю бэкапы локально: " + ",".join(backup_filenames))
        save_local(archive_paths, backup_filenames, _config)

    delete_archives_after_backup = True
    if "DELETE_ARCHIVES_AFTER_BACKUP" in _config.files["config"]:
        delete_archives_after_backup = _config.files["config"]["DELETE_ARCHIVES_AFTER_BACKUP"]

    if delete_archives_after_backup:
        logger.info("Удаляю архивы после бэкапа")
        delete_archives(archive_paths_to_delete)

    if "after_backup_scripts" in _config.files:
        logger.info("Запускаю скрипты после запуска бэкапа")
        launch_scripts(_config.files["after_backup_scripts"], "Скрипт после запуска бэкапа: ")
    logger.info("Завершение бэкапа: " + _config.dir_name)


def launch_scripts(scripts, log_msg=None):
    return_codes = []
    for script in scripts:
        script_result = subprocess.run(script.split(" "), stdout=subprocess.PIPE)
        logger.info(
            log_msg + script + " Вернул код: " + str(
                script_result.returncode) + " Вывод: " + script_result.stdout.decode("utf-8"))
        return_codes.append(script_result.returncode)
    for return_code in return_codes:
        if return_code != 1:
            return False
    return True


def backup_filename_format(_config):
    default_format = "${CONFIGURATION_NAME}-${datetime_format:%d-%m-%Y в %H-%M-%S}.zip"
    _format = None
    if "backup_filename_format" in _config.files:
        if len(_config.files["backup_filename_format"]) > 0:
            _format = _config.files["backup_filename_format"][0]
    if not _format:
        _format = default_format
    filename = _format
    filename = filename.replace("${CONFIGURATION_NAME}", _config.dir_name)
    datetime_format_var_start = "${datetime_format:"
    if datetime_format_var_start in filename:
        start_pos = filename.find(datetime_format_var_start)
        stop_pos = filename.find("}", start_pos)
        datetime_format = filename[start_pos + len(datetime_format_var_start):stop_pos]
    filename = filename.replace(datetime_format_var_start + datetime_format + "}",
                                datetime.datetime.now().strftime(datetime_format))
    return filename


def make_archives(_config):
    backup_filename = backup_filename_format(_config)
    configuration_backups_folder = BACKUPS_PATH + "\\" + _config.dir_name
    if not os.path.exists(configuration_backups_folder):
        os.makedirs(configuration_backups_folder)
    archive_paths = []
    backup_filenames = []
    archive_paths_to_delete = []
    future_data_association_list = []
    make_archive_executor = make_thread_pool_executor(_config, "MAX_MAKE_ARCHIVE_WORKERS")
    make_archive_future_list = []
    for i, backup_path in enumerate(_config.files["path"]):
        backup_filename = str(i + 1) + "-" + backup_filename
        archive_path = configuration_backups_folder + "\\" + backup_filename
        future = make_archive_executor.submit(make_archive, backup_path, backup_filename, archive_path, _config)
        make_archive_future_list.append(future)
        future_data_association_list.append((future, backup_path, backup_filename, archive_path))
    for future in as_completed(make_archive_future_list):
        result = future.result()
        future_data_association = association_list_search(future, future_data_association_list)
        backup_path = future_data_association[1]
        backup_filename = future_data_association[2]
        archive_path = future_data_association[3]
        if result:
            archive_paths.append(archive_path)
            backup_filenames.append(backup_filename)
        else:
            logger.info(
                "Ошибка создания архива бэкапа, пути директории бэкапа: " + backup_path + " Имя бэкапа: " +
                backup_filename + " Путь архива бэкапа: " + archive_path + " Бэкап будет проигнорирован и удален")
        archive_paths_to_delete.append(archive_path)
        make_archive_future_list.remove(future)
    return archive_paths, backup_filenames, archive_paths_to_delete


def make_archive(backup_path, backup_filename, archive_path, _config):
    compression = zipfile.ZIP_STORED

    compression_in_config = None
    if "ZIP_COMPRESSION" in _config.files["config"]:
        compression_in_config = _config.files["config"]["ZIP_COMPRESSION"]

    if compression_in_config == "zlib":
        compression = zipfile.ZIP_DEFLATED
    elif compression_in_config == "bz2":
        compression = zipfile.ZIP_BZIP2
    elif compression_in_config == "lzma":
        compression = zipfile.ZIP_LZMA

    try:
        z = zipfile.ZipFile(archive_path, "w")
    except Exception as e:
        logger.info(
            "Ошибка создания архива бэкапа, пути директории бэкапа: " + backup_path + " Имя бэкапа: " +
            backup_filename + " Путь архива бэкапа: " + archive_path + " Ошибка: " + str(e))
        return False
    for root, dirs, files in os.walk(backup_path):
        for file in files:
            file_path = os.path.join(root, file)
            if "ignore" in _config.files:
                ignore = False
                for ignore_value in _config.files["ignore"]:
                    if is_ignore(backup_path, file_path, ignore_value):
                        ignore = True
                        break
                if not ignore:
                    try:
                        z.write(file_path, compress_type=compression)
                    except Exception as e:
                        logger.info(
                            "Ошибка создания архива бэкапа, пути директории бэкапа: " + backup_path + " Имя бэкапа: " +
                            backup_filename + " Путь архива бэкапа: " + archive_path + " Ошибка: " + str(e))
                        return False
            else:
                try:
                    z.write(file_path, compress_type=compression)
                except Exception as e:
                    logger.info(
                        "Ошибка создания архива бэкапа, пути директории бэкапа: " + backup_path + " Имя бэкапа: " +
                        backup_filename + " Путь архива бэкапа: " + archive_path + " Ошибка: " + str(e))
                    return False
    z.close()
    return True


def is_ignore(backup_path, file_path, ignore_value):
    file_path = normalize_path(file_path)
    if type(ignore_value) is ConfigConstruct:
        for value in ignore_value.values:
            value = normalize_dir(value)
            ignore_path = backup_path + "\\" + ignore_value.name + "\\" + value
            ignore_path = normalize_path(ignore_path)
            if file_path == ignore_path:
                return True
            elif os.path.isdir(ignore_path) and ignore_path in file_path:
                return True
    else:
        ignore_path = backup_path + "\\" + ignore_value
        ignore_path = normalize_path(ignore_path)
        if file_path == ignore_path:
            return True
        elif os.path.isdir(ignore_path) and ignore_path in file_path:
            return True
    return False


def delete_archives(archive_paths):
    for archive_path in archive_paths:
        if os.path.isfile(archive_path):
            os.remove(archive_path)
            logger.info("Удалил архив: " + archive_path)


def upload_backups(archive_paths, backup_filenames, _config):
    servers = []
    if "servers" in _config.files:
        if len(_config.files["servers"]) > 0:
            servers = _config.files["servers"]
    if len(servers) == 0:
        logger.info("Серверов в конфигурации 0. Отменяю загрузку бэкапа")
        return False
    for index, server in enumerate(servers):
        server_found = False
        for server_with_token in main_configs.files["servers"]:
            if server[0] == server_with_token[0]:
                if len(server_with_token) == 1:
                    break
                servers[index] = server_with_token
                server_found = True
                break
        if not server_found:
            logger.info("Не нашел токен пользователя для сервера: " + " ".join(server) + " сервер будет проигнорирован")
            servers.pop(index)
    logger.info("Запускаю загрузку бэкапов")
    uploads_executor = make_thread_pool_executor(_config, "MAX_UPLOAD_WORKERS")
    uploads_future_list = []
    for server in servers:
        for index, archive_path in enumerate(archive_paths):
            backup_filename = backup_filenames[index]
            uploads_future_list.append(
                uploads_executor.submit(upload_backup, archive_path, backup_filename, server, _config))
    completed_uploads_count = 0
    error_uploads_count = 0
    for future in as_completed(uploads_future_list):
        result = future.result()
        if result:
            completed_uploads_count += 1
        else:
            error_uploads_count += 1
        uploads_future_list.remove(future)
    logger.info("Загрузка бэкапов завершена. Количество успешных загрузок: " + str(
        completed_uploads_count) + " Количество загрузок с ошибкой: " + str(error_uploads_count))


def upload_backup(archive_path, backup_filename, server, _config):
    logger.info("Начинаю загрузку файла: " + backup_filename + " на сервер: " + server[0])
    files = {"backup_files": (backup_filename, open(archive_path, "rb"), mimetypes.guess_type(archive_path)[0])}
    try:
        response = requests.post("http://" + server[0] + "/upload_backup", files=files)
    except Exception as e:
        logger.info("Ошибка подключения к серверу: " + server[0] + " Ошибка: " + str(e))
        return False
    if response.status_code == 200:
        response_json = response.json()
        if response_json["success"]:
            logger.info("Успешно загрузил бэкап: " + backup_filename + " на сервер: " + server[
                0] + " ответ сервера: " + response.text)
            return True
        else:
            logger.info("Ошибка при загрузке. Ответ сервера: " + response.text)
    else:
        logger.info("Ошибка при загрузке. Код ответа: " + str(
            response.status_code) + " Причина: " + response.reason + " Ответ сервера: " + response.text)
    return False


def save_local(archive_paths, backup_filenames, _config):
    pass


