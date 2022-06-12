import logging
import datetime
from eaZy_backup.config import LOGS_PATH, SERVER_LOGS_PATH


def configure_logs(log_file_name_format, logs_path):
    now = datetime.datetime.now()
    log_file_name = now.strftime(log_file_name_format)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(logs_path + "\\" + log_file_name),
            logging.StreamHandler()
        ],
        encoding="utf-8"
    )
    return logging.getLogger(__name__)


def configure_client_logs():
    return configure_logs("log-%d-%m-%Y в %H-%M-%S.log", LOGS_PATH)


def configure_server_logs():
    return configure_logs("server-log-%d-%m-%Y в %H-%M-%S.log", SERVER_LOGS_PATH)


