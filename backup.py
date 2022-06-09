import datetime
import os

from config import BACKUPS_PATH
from config_object import ConfigConstruct
from log import logger
import subprocess
import zipfile

from _path import normalize_path, normalize_dir


def backup(_config, time):
    logger.info("Запуск бэкапа: " + _config.dir_name + " Время: " + time)

    if "before_backup_scripts" in _config.files:
        if not launch_scripts(_config.files["before_backup_scripts"], "Скрипт перед запуском бэкапа: "):
            logger.info("Отмена запуска бэкапа. Не все скрипты завершились с кодом 1")

    archive_path = make_archive(_config)

    if "after_backup_scripts" in _config.files:
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

    for i, backup_path in enumerate(_config.files["path"]):
        archive_path = configuration_backups_folder + "\\" + str(i + 1) + "-" + backup_filename
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
                        z.write(file_path)
                else:
                    z.write(file_path)
        z.close()

    return archive_path


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


