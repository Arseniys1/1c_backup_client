from eaZy_backup.association_list_search import association_list_search
from eaZy_backup.config import configs, custom_configs_dirs
from eaZy_backup.log import configure_client_logs
from eaZy_backup.backup import backup
from concurrent.futures import as_completed
from eaZy_backup.logotype import print_logotype
import datetime
import time as _time

from eaZy_backup.parallels import make_thread_pool_executor

logger = configure_client_logs()

logger.info("Найдены директории с файлами конфигурации: " + ",".join(custom_configs_dirs))
for config_obj in configs:
    for file in config_obj.files.keys():
        logger.info("Найден файл конфигурации: " + config_obj.dir_name + " -> " + file)


def main():
    print_logotype()
    _config_data_association_list = []
    for _config in configs:
        _config_data_association_list.append((_config, make_thread_pool_executor(_config, "MAX_BACKUP_WORKERS"), []))
    while True:
        now = datetime.datetime.now()
        now_hours_minutes = now.strftime("%H:%M")
        for _config in configs:
            _config_data_association = association_list_search(_config, _config_data_association_list)
            executor = _config_data_association[1]
            future_list = _config_data_association[2]
            for time in _config.files["time"]:
                backup(_config, time)
                _time.sleep(1000)
                if now_hours_minutes == time or True:
                    future_list.append(executor.submit(backup, _config, time))
                    # _time.sleep(1000)
            for future in as_completed(future_list):
                future.result()
                future_list.remove(future)



if __name__ == '__main__':
    main()

