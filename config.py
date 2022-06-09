from dotenv import dotenv_values
from config_object import Config
import os

from exceptions.ConfigFileNotFound import ConfigFileNotFound

ROOT_DIR = os.path.abspath(os.curdir)
SYSTEM_ROOT_DIR = os.path.abspath(os.sep)
CONFIG_PATH = ROOT_DIR + "\\config.env"
CONFIGS_PATH = ROOT_DIR + "\\configs"
LOGS_PATH = ROOT_DIR + "\\logs"
BACKUPS_PATH = ROOT_DIR + "\\backups"

configs_dirs = [config_dir for config_dir in os.listdir(CONFIGS_PATH) if
                os.path.isdir(CONFIGS_PATH + "\\" + config_dir)]

MAIN_CONFIGS_FILE_NAMES = [
    "path.txt",
    "time.txt",
    "servers.txt",
]

CONFIG_FILE_EXTENSIONS = [
    ".txt",
    ".conf",
]


def load_configs():
    _configs = []
    for config_dir in configs_dirs:
        _configs.append(make_cfg_object_from_dir(config_dir, CONFIGS_PATH + "\\" + config_dir))
    return _configs


def load_config():
    return make_cfg_object_from_dir(os.path.basename(ROOT_DIR), ROOT_DIR, False)


def make_cfg_object_from_dir(config_dir, dir_path, check_main_config_files=True):
    cfg_object = Config(config_dir)
    listdir = os.listdir(dir_path)
    for main_config_file_name in MAIN_CONFIGS_FILE_NAMES:
        if main_config_file_name not in listdir and check_main_config_files:
            raise ConfigFileNotFound(
                "В папке конфигов: " + config_dir + " не найден основной файл: " + main_config_file_name + " создайте его")
    for config_file in listdir:
        config_file_name, config_file_ext = os.path.splitext(config_file)
        if config_file_ext not in CONFIG_FILE_EXTENSIONS:
            continue
        cfg_object.add_file(config_file_name,
                            read_config(config_dir, dir_path + "\\" + config_file))
    return cfg_object


def read_config(config_dir, config_path):
    try:
        with open(config_path, encoding="utf-8") as f:
            lines = f.readlines()
            lines_filtered = []
            for line in lines:
                if line[0] != "#" and line != "\n" and line != "\r\n":
                    lines_filtered.append(replace_in_line(config_dir, line))
            return lines_filtered
    except Exception as e:
        print(e)


def config_types(_config):
    int_keys = ["SERVER_PING_TIMEOUT", "SERVER_PING_TIME", "MAX_WORKERS"]
    bool_keys = ["SERVER_PING", "DELETE_ARCHIVES_AFTER_BACKUP"]
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
    line = line.replace("${ROOT_DIR}", ROOT_DIR)
    line = line.replace("${SYSTEM_ROOT_DIR}", SYSTEM_ROOT_DIR)
    return line


config = dotenv_values(CONFIG_PATH)
config = config_types(config)

configs = load_configs()
main_configs = load_config()


