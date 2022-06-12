from dotenv import dotenv_values
from config_object import Config
import os

from exceptions.ConfigFileNotFound import ConfigFileNotFound

ROOT_DIR = os.path.abspath(os.curdir)
# исправляет ROOT_DIR при запуске скриптов
root_dir_normalized = os.path.normpath(ROOT_DIR)
root_dir_split = root_dir_normalized.split(os.sep)
if root_dir_split[-1] == "scripts":
    ROOT_DIR = os.sep.join(root_dir_split[:-1])

SYSTEM_ROOT_DIR = os.path.abspath(os.sep)
CONFIG_PATH = ROOT_DIR + "\\config.env"
SERVER_CONFIG_PATH = ROOT_DIR + "\\server.env"
FASTAPI_UVICORN_LOG_INI = ROOT_DIR + "\\fastapi_uvicorn_log.ini"
CUSTOM_CONFIGS_PATH = ROOT_DIR + "\\configs"
LOGS_PATH = ROOT_DIR + "\\logs"
SERVER_LOGS_PATH = ROOT_DIR + "\\server_logs"
BACKUPS_PATH = ROOT_DIR + "\\backups"
SERVER_BACKUPS_PATH = ROOT_DIR + "\\server_backups"

custom_configs_dirs = [config_dir for config_dir in os.listdir(CUSTOM_CONFIGS_PATH) if
                       os.path.isdir(CUSTOM_CONFIGS_PATH + "\\" + config_dir)]

MAIN_CUSTOM_CONFIGS_FILE_NAMES = [
    "path",
    "time",
    "servers",
    "config",
]

MAIN_CONFIGS_FILE_NAMES = [
    "server_available_content_types",
    "server_backups_save",
    "clients",
    "servers",
]

CONFIG_FILE_EXTENSIONS = [
    ".txt",
    ".conf",
    ".env",
]


def load_configs(dir_path, check_main_config_files=False, main_config_files=None):
    _configs = []
    configs_dirs = [config_dir for config_dir in os.listdir(dir_path) if
                    os.path.isdir(dir_path + "\\" + config_dir)]
    for config_dir in configs_dirs:
        _configs.append(make_cfg_object_from_dir(config_dir, dir_path + "\\" + config_dir, check_main_config_files,
                                                 main_config_files))
    return _configs


def load_config(config_dir, dir_path, check_main_config_files=False, main_config_files=None):
    return make_cfg_object_from_dir(config_dir, dir_path, check_main_config_files, main_config_files)


def make_cfg_object_from_dir(config_dir, dir_path, check_main_config_files=False, main_config_files=None):
    cfg_object = Config(config_dir)
    listdir = os.listdir(dir_path)
    if check_main_config_files:
        for main_config_file_name in main_config_files:
            main_config_file_names_with_ext = [main_config_file_name + config_file_extension for config_file_extension
                                               in
                                               CONFIG_FILE_EXTENSIONS]
            config_found = False
            for main_config_file_name_with_ext in main_config_file_names_with_ext:
                if main_config_file_name_with_ext in listdir:
                    config_found = True
                    break
            if not config_found:
                raise ConfigFileNotFound(
                    "В папке конфигов: " + config_dir + " не найден основной файл: " + main_config_file_name + " создайте его")
    for config_file in listdir:
        config_file_name, config_file_ext = os.path.splitext(config_file)
        if config_file_ext not in CONFIG_FILE_EXTENSIONS:
            continue
        cfg_object.add_file(config_file_name, config_file_ext, read_config(config_dir, dir_path + "\\" + config_file))
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
    int_keys = ["SERVER_PING_TIMEOUT", "SERVER_PING_TIME", "MAX_BACKUP_WORKERS", "MAX_UPLOAD_WORKERS",
                "MAX_MAKE_ARCHIVE_WORKERS", "SERVER_PORT"]
    bool_keys = ["SERVER_PING", "DELETE_ARCHIVES_AFTER_BACKUP", "UPLOAD_BACKUPS_TO_SERVER"]
    for key in _config.keys():
        for _type_key in int_keys:
            if key == _type_key:
                _config[key] = int(_config[key])
        for _type_key in bool_keys:
            if key == _type_key:
                _config[key] = bool(int(_config[key]))
    return _config


def replace_in_line(config_dir, line):
    line = line.replace("\n", "")
    line = line.replace("\r\n", "")
    line = line.replace("${CURRENT_CONFIG_DIR}", CUSTOM_CONFIGS_PATH + "\\" + config_dir)
    line = line.replace("${ROOT_DIR}", ROOT_DIR)
    line = line.replace("${SYSTEM_ROOT_DIR}", SYSTEM_ROOT_DIR)
    return line


def config_split_line_with_space(file_name, file_lines, dir_path, _config):
    for index, line in enumerate(file_lines):
        file_lines[index] = line.split(" ")
    return file_lines


def config_env_load(file_name, file_lines, dir_path, _config):
    config_env = dotenv_values(dir_path + "\\" + _config.original_file_names[file_name])
    config_env = config_types(config_env)
    return config_env


def config_handlers(dir_path, _config):
    handlers = {
        "clients": [config_split_line_with_space],
        "servers": [config_split_line_with_space],
        "config": [config_env_load],
    }
    for file_name, file_lines in _config.files.items():
        for handler_file_name, func_handlers in handlers.items():
            if file_name == handler_file_name:
                for func_handler in func_handlers:
                    handler_result = func_handler(file_name, file_lines, dir_path, _config)
                    _config.files[file_name] = handler_result
    return _config


def configs_handlers(dir_path, _configs):
    for index, _config in enumerate(_configs):
        _configs[index] = config_handlers(dir_path + "\\" + _config.dir_name, _config)
    return _configs


config = dotenv_values(CONFIG_PATH)
config = config_types(config)

server_config = dotenv_values(SERVER_CONFIG_PATH)
server_config = config_types(server_config)

configs = configs_handlers(CUSTOM_CONFIGS_PATH, load_configs(CUSTOM_CONFIGS_PATH, True, MAIN_CUSTOM_CONFIGS_FILE_NAMES))
main_configs = config_handlers(ROOT_DIR,
                               load_config(os.path.basename(ROOT_DIR), ROOT_DIR, True, MAIN_CONFIGS_FILE_NAMES))
