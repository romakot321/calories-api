from io import BytesIO
from uuid import UUID
from src.task.application.interfaces.task_uow import ITaskUnitOfWork
from src.task.domain.dtos import TaskCreateDTO, TaskCreateWithTextDTO
from src.task.domain.entities import TaskRun


class BuildTaskParamsUseCase:
    def __init__(self, uow: ITaskUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, dto: TaskCreateDTO | TaskCreateWithTextDTO, old_task_id: UUID | None = None, file: BytesIO | None = None) -> TaskRun:
        prev_task_text = await self._build_prev_task_text(old_task_id)
        user_input_text = dto.text if hasattr(dto, 'text') else ''
        return TaskRun(
            file=file,
            text=prev_task_text + user_input_text,
            language=dto.language,
        )

    async def _build_prev_task_text(self, old_task_id: UUID | None) -> str:
        if old_task_id is None:
            return ''
        async with self.uow:
            task = await self.uow.tasks.get_by_pk(old_task_id)
        return '\n'.join(str(p) for p in task.products) + "\n".join(str(s) for s in task.sports)
