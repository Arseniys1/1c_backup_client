from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.post("/upload_backup")
async def upload_backup(backup_file: UploadFile):
    return {"filename": backup_file.filename}

