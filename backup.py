import datetime

from log import logger
import subprocess
import zipfile


def backup(_config, time):
    logger.info("Запуск бэкапа: " + _config.dir_name + " Время: " + time)

    if "before_backup_scripts.txt" in _config.files:
        if not launch_scripts(_config.files["before_backup_scripts.txt"], "Скрипт перед запуском бэкапа: "):
            logger.info("Отмена запуска бэкапа. Не все скрипты завершились с кодом 1")

    backup_filename = backup_filename_format(_config)

    if "after_backup_scripts.txt" in _config.files:
        launch_scripts(_config.files["after_backup_scripts.txt"], "Скрипт после запуска бэкапа: ")
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
    if "backup_filename_format.txt" in _config.files:
        if len(_config.files["backup_filename_format.txt"]) > 0:
            _format = _config.files["backup_filename_format.txt"][0]
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
