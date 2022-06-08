from config import config, ROOT_DIR, CONFIG_PATH, CONFIGS_PATH, LOGS_PATH, configs, configs_dirs
from log import logger


logger.info("Найдены директории с файлами конфигурации: " + ",".join(configs_dirs))
for config_obj in configs:
    for file in config_obj.files.keys():
        logger.info("Найден файл конфигурации: " + config_obj.dir_name + " -> " + file)


def main():
    pass


if __name__ == '__main__':
    main()

