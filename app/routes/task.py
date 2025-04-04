from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    UploadFile,
    File,
    HTTPException,
    status,
)
from uuid import UUID
from . import validate_api_token

from app.services.task import TaskService
from app.schemas.task import (
    Language,
    TaskConsultationCreateSchema,
    TaskConsultationSchema,
    TaskSportSchema,
    TaskEditSchema,
    TaskSchema,
    TaskTextCreateSchema,
)


router = APIRouter(prefix="/api/task", tags=["Meal recognition task"])
max_file_size = 25 * 1024 * 1024


async def _validate_file_size(file: UploadFile = File()) -> UploadFile:
    body = await file.read()
    if len(body) > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size is too big. Limit is 25mb",
        )
    await file.seek(0)
    return file


def _validate_file_is_image(
    file: UploadFile = Depends(_validate_file_size),
) -> UploadFile:
    accepted_file_types = [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/heic",
        "image/heif",
        "image/heics",
        "png",
        "jpeg",
        "jpg",
        "heic",
        "heif",
        "heics",
    ]
    return file

    if file.content_type not in accepted_file_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type for image",
        )
    return file


def _validate_file_is_audio(
    file: UploadFile = Depends(_validate_file_size),
) -> UploadFile:
    accepted_file_types = [
        "audio/mpeg",
        "video/mp4",
        "video/mpeg",
        "audio/ogg",
        "audio/wav",
        "audio/webm",
        "video/webm",
        "video/ogg",
    ]
    return file

    if file.content_type not in accepted_file_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type for audio",
        )
    return file


@router.post("/text/meal", response_model=TaskSchema)
async def create_text_meal_task(
    background_tasks: BackgroundTasks,
    schema: TaskTextCreateSchema,
    _=Depends(validate_api_token),
    service: TaskService = Depends(),
):
    model = await service.create()
    background_tasks.add_task(service.send_text, model.id, schema)
    return model


@router.post("/text/sport", response_model=TaskSchema)
async def create_text_sport_task(
    background_tasks: BackgroundTasks,
    schema: TaskTextCreateSchema,
    _=Depends(validate_api_token),
    service: TaskService = Depends(),
):
    model = await service.create()
    background_tasks.add_task(service.send_text_sport, model.id, schema)
    return model


@router.post("/image", response_model=TaskSchema)
async def create_image_task(
    background_tasks: BackgroundTasks,
    language: Language = Query(Language.russian),
    _=Depends(validate_api_token),
    file: UploadFile = Depends(_validate_file_is_image),
    service: TaskService = Depends(),
):
    model = await service.create()
    background_tasks.add_task(service.send, model.id, await file.read(), language)
    return model


@router.post("/audio/meal", response_model=TaskSchema)
async def create_audio_task(
    background_tasks: BackgroundTasks,
    _=Depends(validate_api_token),
    file: UploadFile = Depends(_validate_file_is_audio),
    service: TaskService = Depends(),
):
    model = await service.create()
    background_tasks.add_task(
        service.send_audio, model.id, await file.read(), Language.russian
    )
    return model


@router.post("/audio/sport", response_model=TaskSchema)
async def create_audio_sport_task(
    background_tasks: BackgroundTasks,
    _=Depends(validate_api_token),
    file: UploadFile = Depends(_validate_file_is_audio),
    service: TaskService = Depends(),
):
    model = await service.create()
    background_tasks.add_task(
        service.send_sport_audio, model.id, await file.read(), Language.russian
    )
    return model


@router.get("/image/{task_id}", response_model=TaskSchema)
async def get_image_task(
    task_id: UUID, _=Depends(validate_api_token), service: TaskService = Depends()
):
    return await service.get(task_id)


@router.get("/audio/meal/{task_id}", response_model=TaskSchema)
async def get_audio_meal_task(
    task_id: UUID, _=Depends(validate_api_token), service: TaskService = Depends()
):
    return await service.get(task_id)


@router.get("/audio/sport/{task_id}", response_model=TaskSportSchema)
async def get_audio_sport_task(
    task_id: UUID, _=Depends(validate_api_token), service: TaskService = Depends()
):
    return await service.get(task_id)


@router.get("/text/meal/{task_id}", response_model=TaskSchema)
async def get_text_meal_task(
    task_id: UUID, _=Depends(validate_api_token), service: TaskService = Depends()
):
    return await service.get(task_id)


@router.get("/text/sport/{task_id}", response_model=TaskSportSchema)
async def get_text_sport_task(
    task_id: UUID, _=Depends(validate_api_token), service: TaskService = Depends()
):
    return await service.get(task_id)


@router.post("/{task_id}/edit", response_model=TaskSchema)
async def edit_task(
    task_id: UUID,
    background_tasks: BackgroundTasks,
    schema: TaskEditSchema,
    _=Depends(validate_api_token),
    service: TaskService = Depends(),
):
    """Update meal with provided user input and create new task. For example, replace tunica with salmon"""
    await service.get(task_id)
    model = await service.create()
    background_tasks.add_task(service.send_edit, task_id, model.id, schema)
    return model


@router.post("/{task_id}/edit/sport", response_model=TaskSportSchema)
async def edit_sport_task(
    task_id: UUID,
    background_tasks: BackgroundTasks,
    schema: TaskEditSchema,
    _=Depends(validate_api_token),
    service: TaskService = Depends(),
):
    await service.get(task_id)
    model = await service.create()
    background_tasks.add_task(service.send_edit_sport, task_id, model.id, schema)
    return model


@router.post("/consultation", response_model=TaskConsultationSchema)
async def get_consultation(
    schema: TaskConsultationCreateSchema,
    _=Depends(validate_api_token),
    service: TaskService = Depends(),
):
    return await service.get_consultation(schema)
