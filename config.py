from dotenv import dotenv_values
from config_object import Config
import os


ROOT_DIR = os.path.abspath(os.curdir)
CONFIG_PATH = ROOT_DIR + "\\config.env"
CONFIGS_PATH = ROOT_DIR + "\\configs"
LOGS_PATH = ROOT_DIR + "\\logs"

config = dotenv_values(CONFIG_PATH)
configs_dirs = [config_dir for config_dir in os.listdir(CONFIGS_PATH) if os.path.isdir(CONFIGS_PATH + "\\" + config_dir)]


def load_configs():
    _configs = []
    for config_dir in configs_dirs:
        cfg_object = Config(config_dir)
        for config_file in os.listdir(CONFIGS_PATH + "\\" + config_dir):
            with open(CONFIGS_PATH + "\\" + config_dir + "\\" + config_file, encoding="utf-8") as f:
                lines = f.readlines()
                lines_filtered = []
                for line in lines:
                    if line[0] != "#" and line != "\n" and line != "\r\n":
                        line = line.replace("\n", "")
                        line = line.replace("\r\n", "")
                        lines_filtered.append(line)
                cfg_object.add_file(config_file, lines_filtered)
        _configs.append(cfg_object)
    return _configs


configs = load_configs()


