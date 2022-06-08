from config import config, ROOT_DIR, CONFIG_PATH, CONFIGS_PATH, LOGS_PATH, configs, configs_dirs
from log import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime


logger.info("Найдены директории с файлами конфигурации: " + ",".join(configs_dirs))
for config_obj in configs:
    for file in config_obj.files.keys():
        logger.info("Найден файл конфигурации: " + config_obj.dir_name + " -> " + file)


def main():
    while True:
        now = datetime.datetime.now()
        now_hours_minutes = now.strftime("%H:%M")
        for _config in configs:
            for time in _config.files["time.txt"]:
                if now_hours_minutes == time:
                    pass


if __name__ == '__main__':
    main()

