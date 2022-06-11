from config import config, ROOT_DIR, CONFIG_PATH, CUSTOM_CONFIGS_PATH, LOGS_PATH, configs, custom_configs_dirs
from log import configure_client_logs
from backup import backup, launch_scripts
from concurrent.futures import ThreadPoolExecutor, as_completed
from logotype import print_logotype
import datetime
import time as _time

logger = configure_client_logs()

logger.info("Найдены директории с файлами конфигурации: " + ",".join(custom_configs_dirs))
for config_obj in configs:
    for file in config_obj.files.keys():
        logger.info("Найден файл конфигурации: " + config_obj.dir_name + " -> " + file)


executor = ThreadPoolExecutor(max_workers=config["MAX_WORKERS"])
future_list = []


def main():
    print_logotype()
    while True:
        now = datetime.datetime.now()
        now_hours_minutes = now.strftime("%H:%M")
        for _config in configs:
            for time in _config.files["time"]:
                # backup(_config, time)
                if now_hours_minutes == time or True:
                    future_list.append(executor.submit(backup, _config, time))
                    _time.sleep(1000)


if __name__ == '__main__':
    main()

