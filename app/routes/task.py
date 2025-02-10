from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File
from uuid import UUID
from . import validate_api_token

from app.services.task import TaskService
from app.schemas.task import TaskSchema


router = APIRouter(prefix="/api/task", tags=["Meal recognition task"])


@router.post("/", response_model=TaskSchema)
async def create_task(
        background_tasks: BackgroundTasks,
        _=Depends(validate_api_token),
        file: UploadFile = File(),
        service: TaskService = Depends()
):
    model = await service.create()
    background_tasks.add_task(service.send, model.id, file.file.read())
    return model


@router.get("/{task_id}", response_model=TaskSchema)
async def get_task(
        task_id: UUID,
        _=Depends(validate_api_token),
        service: TaskService = Depends()
):
    return await service.get(task_id)

