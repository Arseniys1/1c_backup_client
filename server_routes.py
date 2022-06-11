from fastapi import APIRouter, UploadFile
from typing import List

router = APIRouter()


@router.post("/upload_backup")
async def upload_backup(backup_files: List[UploadFile]):
    return {"success": True, "filenames": [backup_file.filename for backup_file in backup_files]}
