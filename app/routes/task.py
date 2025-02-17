from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException, status
from uuid import UUID
from . import validate_api_token

from app.services.task import TaskService
from app.schemas.task import TaskAudioSchema, TaskSchema


router = APIRouter(prefix="/api/task", tags=["Meal recognition task"])
max_file_size = 25 * 1024 * 1024


async def _validate_file_size(file: UploadFile = File()) -> UploadFile:
    body = await file.read()
    if len(body) > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size is too big. Limit is 25mb"
        )
    await file.seek(0)
    return file


def _validate_file_is_image(file: UploadFile = Depends(_validate_file_size)) -> UploadFile:
    accepted_file_types = [
        "image/png", "image/jpeg", "image/jpg", "image/heic", "image/heif", "image/heics", "png",
        "jpeg", "jpg", "heic", "heif", "heics"
    ]

    if file.content_type not in accepted_file_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type for image",
        )
    return file


def _validate_file_is_audio(file: UploadFile = Depends(_validate_file_size)) -> UploadFile:
    accepted_file_types = [
        "audio/mpeg", "video/mp4", "video/mpeg", "audio/ogg", "audio/wav",
        "audio/webm", "video/webm"
    ]

    if file.content_type not in accepted_file_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type for image",
        )
    return file


@router.post("/image", response_model=TaskSchema)
async def create_image_task(
        background_tasks: BackgroundTasks,
        _=Depends(validate_api_token),
        file: UploadFile = Depends(_validate_file_is_image),
        service: TaskService = Depends()
):
    model = await service.create()
    background_tasks.add_task(service.send, model.id, file.file.read())
    return model


@router.post("/audio", response_model=TaskAudioSchema)
async def create_audio_task(
        background_tasks: BackgroundTasks,
        _=Depends(validate_api_token),
        file: UploadFile = Depends(_validate_file_is_audio),
        service: TaskService = Depends()
):
    model = await service.create()


@router.get("/{task_id}", response_model=TaskSchema)
async def get_task(
        task_id: UUID,
        _=Depends(validate_api_token),
        service: TaskService = Depends()
):
    return await service.get(task_id)

