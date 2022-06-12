from eaZy_backup.config import server_config, \
    FASTAPI_UVICORN_LOG_INI
from eaZy_backup.log import configure_server_logs
from fastapi import FastAPI
from eaZy_backup.server.server_routes import router as server_routes_router
from eaZy_backup.logotype import print_logotype
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
