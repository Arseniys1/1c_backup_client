import logging
from config import LOGS_PATH
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_PATH + "\\debug.log"),
        logging.StreamHandler()
    ],
    encoding="utf-8"
)
logger = logging.getLogger("main")