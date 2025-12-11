from src.task.domain.entities import TaskRun
from src.integration.domain.schemas import OpenaiRunRequest


class TaskRunToRequestMapper:
    def map_one(self, task_run: TaskRun, file_id: str) -> OpenaiRunRequest:
        pass
