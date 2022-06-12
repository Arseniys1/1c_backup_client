import datetime
import os

from config import BACKUPS_PATH, config, main_configs
from config_object import ConfigConstruct
from log import configure_client_logs
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import zipfile
import requests
import mimetypes

from _path import normalize_path, normalize_dir

logger = configure_client_logs()

compression = zipfile.ZIP_STORED

if config["ZIP_COMPRESSION"] == "zlib":
    compression = zipfile.ZIP_DEFLATED
elif config["ZIP_COMPRESSION"] == "bz2":
    compression = zipfile.ZIP_BZIP2
elif config["ZIP_COMPRESSION"] == "lzma":
    compression = zipfile.ZIP_LZMA

uploads_executor = ThreadPoolExecutor(max_workers=config["MAX_UPLOAD_WORKERS"])
uploads_future_list = []


def backup(_config, time):
    logger.info("Запуск бэкапа: " + _config.dir_name + " Время: " + time)

    if "before_backup_scripts" in _config.files:
        logger.info("Запускаю скрипты перед запуском бэкапа")
        if not launch_scripts(_config.files["before_backup_scripts"], "Скрипт перед запуском бэкапа: "):
            logger.info("Отмена запуска бэкапа. Не все скрипты завершились с кодом 1")

    archive_paths, backup_filenames = make_archive(_config)

    if _config.files["config"]["UPLOAD_BACKUPS_TO_SERVER"]:
        upload_backups_result = upload_backups(archive_paths, backup_filenames, _config)

    if config["DELETE_ARCHIVES_AFTER_BACKUP"]:
        logger.info("Удаляю архивы после бэкапа")
        delete_archives(archive_paths)

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


def make_archive(_config):
    backup_filename = backup_filename_format(_config)
    configuration_backups_folder = BACKUPS_PATH + "\\" + _config.dir_name
    if not os.path.exists(configuration_backups_folder):
        os.makedirs(configuration_backups_folder)
    archive_paths = []
    backup_filenames = []
    for i, backup_path in enumerate(_config.files["path"]):
        backup_filename = str(i + 1) + "-" + backup_filename
        archive_path = configuration_backups_folder + "\\" + backup_filename
        z = zipfile.ZipFile(archive_path, "w")
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
                        z.write(file_path, compress_type=compression)
                else:
                    z.write(file_path, compress_type=compression)
        archive_paths.append(archive_path)
        backup_filenames.append(backup_filename)
        z.close()
    return archive_paths, backup_filenames


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
