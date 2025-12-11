from io import BytesIO
from uuid import UUID

from fastapi import File, Depends, APIRouter, UploadFile, BackgroundTasks

from src.core.auth import get_current_user_id
from src.task.application.use_cases.build_task_params import BuildTaskParamsUseCase
from src.task.domain.dtos import TaskCreateWithTextDTO, TaskReadDTO, TaskCreateDTO
from src.task.api.dependencies import (
    TaskAudioMealRunnerDepend,
    TaskAudioSportRunnerDepend,
    TaskEditMealRunnerDepend,
    TaskEditSportRunnerDepend,
    TaskTextMealRunnerDepend,
    TaskTextSportRunnerDepend,
    TaskUoWDepend,
    HttpClientDepend,
    TaskImageMealRunnerDepend,
)
from src.task.application.use_cases.get_task import GetTaskUseCase
from src.task.application.use_cases.run_task import RunTaskUseCase
from src.task.application.use_cases.create_task import CreateTaskUseCase

router = APIRouter()


@router.post("/image/meal", response_model=TaskReadDTO)
async def create_and_run_meal_from_image_task(
    uow: TaskUoWDepend,
    http_client: HttpClientDepend,
    runner: TaskImageMealRunnerDepend,
    background_tasks: BackgroundTasks,
    data: TaskCreateDTO = Depends(TaskCreateDTO.as_form),
    user_id: UUID = Depends(get_current_user_id),
    file: UploadFile = File(),
):
    file_buffer = BytesIO(await file.read())
    file_buffer.name = file.filename
    task = await CreateTaskUseCase(uow).execute(user_id, data, file_buffer)
    cmd = await BuildTaskParamsUseCase(uow).execute(data, None, file_buffer)
    background_tasks.add_task(RunTaskUseCase(uow, runner, http_client).execute, task.id, data.webhook_url, cmd)
    return task


@router.post("/text/meal", response_model=TaskReadDTO)
async def create_and_run_meal_from_text_task(
    uow: TaskUoWDepend,
    http_client: HttpClientDepend,
    runner: TaskTextMealRunnerDepend,
    background_tasks: BackgroundTasks,
    data: TaskCreateWithTextDTO = Depends(TaskCreateWithTextDTO.as_form),
    user_id: UUID = Depends(get_current_user_id),
):
    task = await CreateTaskUseCase(uow).execute(user_id, data, None)
    cmd = await BuildTaskParamsUseCase(uow).execute(data)
    background_tasks.add_task(RunTaskUseCase(uow, runner, http_client).execute, task.id, data.webhook_url, cmd)
    return task


@router.post("/text/sport", response_model=TaskReadDTO)
async def create_and_run_sport_from_text_task(
    uow: TaskUoWDepend,
    http_client: HttpClientDepend,
    runner: TaskTextSportRunnerDepend,
    background_tasks: BackgroundTasks,
    data: TaskCreateWithTextDTO = Depends(TaskCreateWithTextDTO.as_form),
    user_id: UUID = Depends(get_current_user_id),
):
    task = await CreateTaskUseCase(uow).execute(user_id, data, None)
    cmd = await BuildTaskParamsUseCase(uow).execute(data)
    background_tasks.add_task(RunTaskUseCase(uow, runner, http_client).execute, task.id, data.webhook_url, cmd)
    return task


@router.post("/audio/meal", response_model=TaskReadDTO)
async def create_and_run_meal_from_audio_task(
    uow: TaskUoWDepend,
    http_client: HttpClientDepend,
    runner: TaskAudioMealRunnerDepend,
    background_tasks: BackgroundTasks,
    data: TaskCreateDTO = Depends(TaskCreateDTO.as_form),
    user_id: UUID = Depends(get_current_user_id),
    file: UploadFile = File(),
):
    file_buffer = BytesIO(await file.read())
    file_buffer.name = file.filename
    task = await CreateTaskUseCase(uow).execute(user_id, data, file_buffer)
    cmd = await BuildTaskParamsUseCase(uow).execute(data, None, file_buffer)
    background_tasks.add_task(RunTaskUseCase(uow, runner, http_client).execute, task.id, data.webhook_url, cmd)
    return task


@router.post("/audio/sport", response_model=TaskReadDTO)
async def create_and_run_sport_from_audio_task(
    uow: TaskUoWDepend,
    http_client: HttpClientDepend,
    runner: TaskAudioSportRunnerDepend,
    background_tasks: BackgroundTasks,
    data: TaskCreateDTO = Depends(TaskCreateDTO.as_form),
    user_id: UUID = Depends(get_current_user_id),
    file: UploadFile = File(),
):
    file_buffer = BytesIO(await file.read())
    file_buffer.name = file.filename
    task = await CreateTaskUseCase(uow).execute(user_id, data, file_buffer)
    cmd = await BuildTaskParamsUseCase(uow).execute(data, None, file_buffer)
    background_tasks.add_task(RunTaskUseCase(uow, runner, http_client).execute, task.id, data.webhook_url, cmd)
    return task


@router.post("/edit/{task_id}/sport", response_model=TaskReadDTO)
async def create_and_run_edit_sport_task(
    uow: TaskUoWDepend,
    http_client: HttpClientDepend,
    runner: TaskEditSportRunnerDepend,
    background_tasks: BackgroundTasks,
    task_id: UUID,
    data: TaskCreateWithTextDTO = Depends(TaskCreateWithTextDTO.as_form),
    user_id: UUID = Depends(get_current_user_id),
):
    task = await CreateTaskUseCase(uow).execute(user_id, data, None)
    cmd = await BuildTaskParamsUseCase(uow).execute(data, task_id)
    background_tasks.add_task(RunTaskUseCase(uow, runner, http_client).execute, task.id, data.webhook_url, cmd)
    return task


@router.post("/edit/{task_id}/meal", response_model=TaskReadDTO)
async def create_and_run_edit_sport_meal(
    uow: TaskUoWDepend,
    http_client: HttpClientDepend,
    runner: TaskEditMealRunnerDepend,
    background_tasks: BackgroundTasks,
    task_id: UUID,
    data: TaskCreateWithTextDTO = Depends(TaskCreateWithTextDTO.as_form),
    user_id: UUID = Depends(get_current_user_id),
):
    task = await CreateTaskUseCase(uow).execute(user_id, data, None)
    cmd = await BuildTaskParamsUseCase(uow).execute(data, task_id)
    background_tasks.add_task(RunTaskUseCase(uow, runner, http_client).execute, task.id, data.webhook_url, cmd)
    return task


@router.get("/{task_id}", response_model=TaskReadDTO)
async def get_task(task_id: UUID, uow: TaskUoWDepend, _: UUID = Depends(get_current_user_id)):
    return await GetTaskUseCase(uow).execute(task_id)
