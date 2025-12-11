from io import BytesIO
from uuid import UUID, uuid4
from fastapi import HTTPException
from loguru import logger

from src.task.domain.dtos import TaskCreateWithTextDTO, TaskReadDTO, TaskCreateDTO
from src.task.domain.entities import TaskCreate
from src.task.application.interfaces.task_uow import ITaskUnitOfWork


class CreateTaskUseCase:
    def __init__(self, uow: ITaskUnitOfWork):
        self.uow = uow

    async def execute(
        self, user_id: UUID, dto: TaskCreateDTO | TaskCreateWithTextDTO, file: BytesIO | None
    ) -> TaskReadDTO:
        command = TaskCreate(
            **dto.model_dump(exclude={"text"}),
            user_id=user_id,
            request_text=dto.text if isinstance(dto, TaskCreateWithTextDTO) else None,
            request_filename=self._save_file(file),
        )
        async with self.uow:
            task = await self.uow.tasks.create(command)
            await self.uow.commit()
        logger.debug(f"Created {task=}")
        return TaskReadDTO(**task.model_dump())

    def _save_file(self, file: BytesIO | None) -> str | None:
        if file is None:
            return None

        extension = ""
        if "." in (file.name or ""):
            extension = "." + file.name.rsplit(".", 1)[-1]
        file.name = str(uuid4()) + extension

        with open(f"storage/{file.name}", "wb") as f:
            f.write(file.read())

        return file.name
