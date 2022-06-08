from dotenv import dotenv_values
from config_object import Config
import os

from exceptions.ConfigFileNotFound import ConfigFileNotFound

ROOT_DIR = os.path.abspath(os.curdir)
CONFIG_PATH = ROOT_DIR + "\\config.env"
CONFIGS_PATH = ROOT_DIR + "\\configs"
LOGS_PATH = ROOT_DIR + "\\logs"

configs_dirs = [config_dir for config_dir in os.listdir(CONFIGS_PATH) if
                os.path.isdir(CONFIGS_PATH + "\\" + config_dir)]

MAIN_CONFIGS_FILE_NAMES = [
    "path.txt",
    "time.txt",
]


def load_configs():
    _configs = []
    for config_dir in configs_dirs:
        cfg_object = Config(config_dir)
        listdir = os.listdir(CONFIGS_PATH + "\\" + config_dir)
        for main_config_file_name in MAIN_CONFIGS_FILE_NAMES:
            if main_config_file_name not in listdir:
                raise ConfigFileNotFound(
                    "В папке конфигов: " + config_dir + " не найден основной файл: " + main_config_file_name + " создайте его")
        for config_file in listdir:
            if config_file == "scripts":
                continue
            with open(CONFIGS_PATH + "\\" + config_dir + "\\" + config_file, encoding="utf-8") as f:
                lines = f.readlines()
                lines_filtered = []
                for line in lines:
                    if line[0] != "#" and line != "\n" and line != "\r\n":
                        lines_filtered.append(replace_in_line(config_dir, line))
                cfg_object.add_file(config_file, lines_filtered)
        _configs.append(cfg_object)
    return _configs


def config_types(_config):
    int_keys = ["SERVER_PING_TIMEOUT", "SERVER_PING_TIME", "MAX_WORKERS"]
    bool_keys = ["SERVER_PING"]
    for key in _config.keys():
        for _type_key in int_keys:
            if key == _type_key:
                _config[key] = int(_config[key])
        for _type_key in bool_keys:
            if key == _type_key:
                _config[key] = bool(_config[key])
    return _config


def replace_in_line(config_dir, line):
    line = line.replace("\n", "")
    line = line.replace("\r\n", "")
    line = line.replace("${CURRENT_CONFIG_DIR}", CONFIGS_PATH + "\\" + config_dir)
    return line


config = dotenv_values(CONFIG_PATH)
config = config_types(config)

configs = load_configs()
