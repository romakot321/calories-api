import asyncio
from io import BytesIO
from uuid import UUID

from loguru import logger
from pydantic import HttpUrl

from src.core.http.client import IHttpClient
from src.task.domain.dtos import TaskCreateWithTextDTO, TaskReadDTO, TaskCreateDTO, TaskResultDTO
from src.task.domain.mappers import IntegrationResponseToDomainMapper
from src.task.domain.entities import Task, TaskProduct, TaskRun, TaskSport, TaskStatus, TaskUpdate
from src.integration.domain.exceptions import IntegrationRequestException
from src.task.application.interfaces.task_uow import ITaskUnitOfWork
from src.task.application.interfaces.task_runner import ITaskRunner


class RunTaskUseCase:
    TIMEOUT_SECONDS = 5 * 60

    def __init__(
        self,
        uow: ITaskUnitOfWork,
        runner: ITaskRunner,
        http_client: IHttpClient,
    ) -> None:
        self.uow = uow
        self.runner = runner
        self.http_client = http_client

    async def execute(self, task_id: UUID, webhook_url: str | None, command: TaskRun) -> None:
        """Run it in background"""
        logger.info(f"Running task {task_id}")
        logger.debug(f"Task {task_id} params: {command}")
        result, error = await self._run(command)

        if error is not None or result is None:
            result = await self._store_error(task_id, status=TaskStatus.failed, error=error)
            await self._send_webhook(task_id, TaskResultDTO(**result.model_dump()), webhook_url)
            return

        logger.info(f"Task {task_id} result: {result}")
        result = await self._store_result(task_id, result)
        await self._send_webhook(task_id, TaskResultDTO(**result.model_dump()), webhook_url)

    async def _send_webhook(self, task_id: UUID, result: TaskResultDTO, webhook_url: HttpUrl | None):
        if webhook_url is None:
            return
        data = TaskReadDTO(id=task_id, **result.model_dump())
        response = await self.http_client.post(str(webhook_url), json=data.model_dump(mode="json"))
        logger.debug(f"Sended webhook {task_id=}: {response}")

    async def _store_result(self, task_id: UUID, result: TaskResultDTO) -> Task:
        async with self.uow:
            task = await self.uow.tasks.update_by_pk(
                task_id,
                TaskUpdate(
                    status=result.status,
                    error=result.error,
                    products=[TaskProduct(**p.model_dump(mode="json")) for p in result.products],
                    sports=[TaskSport(**s.model_dump(mode="json")) for s in result.sports]
                ),
            )
            await self.uow.commit()
        return task

    async def _store_error(self, task_id: UUID, status: TaskStatus, error: str | None = None) -> Task:
        async with self.uow:
            task = await self.uow.tasks.update_by_pk(task_id, TaskUpdate(status=status, error=error))
            await self.uow.commit()
        return task

    async def _run(self, command: TaskRun) -> tuple[TaskResultDTO | None, None | str]:
        try:
            result = await asyncio.wait_for(self.runner.start(command), timeout=self.TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            return None, "Generation run error: Timeout"
        except IntegrationRequestException as e:
            logger.opt(exception=True).warning(e)
            return None, "Request error: " + str(e)
        except Exception as e:
            logger.exception(e)
            return None, "Internal exception"

        result_domain = IntegrationResponseToDomainMapper().map_one(result)
        return result_domain, None
