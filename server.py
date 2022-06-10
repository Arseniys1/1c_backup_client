from config import config, ROOT_DIR, CONFIG_PATH, CONFIGS_PATH, LOGS_PATH, configs, configs_dirs, server_config, \
    FASTAPI_UVICORN_LOG_INI
from log import configure_server_logs
from fastapi import FastAPI
import uvicorn

logger = configure_server_logs()

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


def main():
    uvicorn.run(app, host=server_config["SERVER_HOST"], port=server_config["SERVER_PORT"],
                log_config=FASTAPI_UVICORN_LOG_INI)


if __name__ == '__main__':
    main()
