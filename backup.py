import datetime
import os

from config import BACKUPS_PATH
from log import logger
import subprocess
import zipfile


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
    default_format = "${CONFIGURATION_NAME}-${datetime_format:%m/%d/%Y, %H:%M:%S}.zip"
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
    archive_path = configuration_backups_folder + "\\" + backup_filename
    if not os.path.exists(configuration_backups_folder):
        os.makedirs(configuration_backups_folder)

    for backup_path in _config.files["path"]:
        z = zipfile.ZipFile(archive_path, "w")
        for root, dirs, files in os.walk(backup_path):
            for file in files:
                file_path = os.path.join(root, file)
                z.write(file_path)
        z.close()

    return archive_path


def normalize_path(path):
    path = os.path.normcase(path)
    path = os.path.normpath(path)
    path = os.path.realpath(path)
    return path


