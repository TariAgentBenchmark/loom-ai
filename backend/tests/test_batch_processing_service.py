from app.models.task import Task, TaskType
from app.services.batch_processing_service import BatchProcessingService


def test_batch_concurrency_defaults_to_three_for_regular_tasks():
    service = BatchProcessingService()
    tasks = [
        Task(type=TaskType.EXTRACT_PATTERN.value, options={"pattern_type": "combined"}),
        Task(type=TaskType.UPSCALE.value, options={}),
    ]

    assert service._resolve_batch_concurrency(tasks) == 3


def test_batch_concurrency_is_one_for_combined_t2_tasks():
    service = BatchProcessingService()
    tasks = [
        Task(type=TaskType.EXTRACT_PATTERN.value, options={"pattern_type": "combined_t2"}),
        Task(type=TaskType.EXTRACT_PATTERN.value, options={"pattern_type": "combined_t2"}),
    ]

    assert service._resolve_batch_concurrency(tasks) == 1
