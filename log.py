import logging
import datetime
from config import LOGS_PATH
now = datetime.datetime.now()
log_file_name = now.strftime("log-%d-%m-%Y в %H-%M-%S.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_PATH + "\\" + log_file_name),
        logging.StreamHandler()
    ],
    encoding="utf-8"
)
logger = logging.getLogger(__name__)