from concurrent.futures import ThreadPoolExecutor


def make_thread_pool_executor(_config, max_workers_key):
    max_workers = 2
    if max_workers_key in _config.files["config"]:
        max_workers = _config.files["config"][max_workers_key]
    return ThreadPoolExecutor(max_workers=max_workers)


