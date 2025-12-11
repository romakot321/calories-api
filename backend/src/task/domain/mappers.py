import json

from pydantic import ValidationError
from src.task.domain.dtos import TaskProductDTO, TaskResultDTO, TaskSportDTO
from src.task.domain.entities import TaskStatus
from src.integration.domain.dtos import IntegrationTaskStatus, IntegrationTaskResultDTO


class IntegrationResponseToDomainMapper:
    def map_one(self, data: IntegrationTaskResultDTO) -> TaskResultDTO:
        products, sports = self._map_result(data.result)

        return TaskResultDTO(
            external_task_id=data.external_task_id,
            status=self._map_status(data.status),
            error=data.error,
            products=products,
            sports=sports
        )

    def _map_result(self, result: list[dict] | None) -> tuple[list[TaskProductDTO], list[TaskSportDTO]]:
        products, sports = [], []
        try:
            products = [TaskProductDTO(**product) for product in result or []]
        except ValidationError:
            pass
        try:
            sports = [TaskSportDTO(**sport) for sport in result or []]
        except ValidationError:
            pass

        if result and not products and not sports:
            raise ValueError("Unknown result")

        return products, sports

    def _map_status(self, status: IntegrationTaskStatus) -> TaskStatus:
        if status == IntegrationTaskStatus.queued:
            return TaskStatus.queued
        elif status == IntegrationTaskStatus.started:
            return TaskStatus.started
        elif status == IntegrationTaskStatus.failed:
            return TaskStatus.failed
        elif status == IntegrationTaskStatus.finished:
            return TaskStatus.finished
        raise ValueError(f"Failed to map integration response: Unknown status {status}")

