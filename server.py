from config import config, ROOT_DIR, CONFIG_PATH, CONFIGS_PATH, LOGS_PATH, configs, configs_dirs, server_config, \
    main_configs, \
    FASTAPI_UVICORN_LOG_INI
from log import configure_server_logs
from fastapi import FastAPI
from server_routes import router as server_routes_router
from logotype import print_logotype
import uvicorn

logger = configure_server_logs()

app = FastAPI()
app.include_router(server_routes_router)


def main():
    print_logotype()
    uvicorn.run(app, host=server_config["SERVER_HOST"], port=server_config["SERVER_PORT"],
                log_config=FASTAPI_UVICORN_LOG_INI)


if __name__ == '__main__':
    main()
