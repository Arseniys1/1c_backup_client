from fastapi import APIRouter, UploadFile
from typing import List
from eaZy_backup.config import main_configs, SERVER_BACKUPS_PATH
from eaZy_backup.log import configure_server_logs
from eaZy_backup.server.server_validation import check_content_types
from eaZy_backup.server.server_api_responses import success_response, error_response
import aiofiles

logger = configure_server_logs()

router = APIRouter()


@router.post("/upload_backup")
async def upload_backup(backup_files: List[UploadFile]):
    available_content_types = main_configs.files["server_available_content_types"]
    passed_files, wrong_files = check_content_types(backup_files, available_content_types)
    if len(backup_files) != len(passed_files):
        wrong_file_names = [wrong_file.filename for wrong_file in wrong_files]
        logger.info(
            "Файлы не прошли проверку content_type: " + ",".join(wrong_file_names))
        return error_response({
            "wrong_file_names": wrong_file_names,
            "available_content_types": available_content_types,
        }, "Не прошли проверку content_type")
    filenames = [backup_file.filename for backup_file in backup_files]
    logger.info("Получил новые бэкапы: " + ",".join(filenames))
    server_backups_path = SERVER_BACKUPS_PATH
    if "server_backups_save" in main_configs.files:
        if len(main_configs.files["server_backups_save"]) > 0:
            server_backups_path = main_configs.files["server_backups_save"][0]
    for backup_file in backup_files:
        async with aiofiles.open(server_backups_path + "\\" + backup_file.filename, 'wb') as backup_file_out:
            content = await backup_file.read()
            await backup_file_out.write(content)
    logger.info("Сохранил бэкапы в директорию: " + server_backups_path)
    return success_response({
        "filenames": filenames
    }, "Сохранил бэкапы")
