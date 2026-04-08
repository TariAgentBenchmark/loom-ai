from app.models.task import Task, TaskType
from app.services.credit_math import to_decimal
from app.services.processing_service import ProcessingService


def _build_task(*, pattern_type: str, num_images=None, credits_used="1.0") -> Task:
    options = {"pattern_type": pattern_type}
    if num_images is not None:
        options["num_images"] = num_images

    return Task(
        task_id="task_extract_pattern_test",
        user_id=1,
        type=TaskType.EXTRACT_PATTERN.value,
        status="processing",
        original_image_url="/files/originals/test.png",
        original_filename="test.png",
        original_file_size=123,
        credits_used=to_decimal(credits_used),
        options=options,
    )


def test_three_extract_pattern_results_do_not_apply_credit_adjustment():
    service = ProcessingService()
    task = _build_task(pattern_type="combined", credits_used="1.0")

    adjustment = service._apply_partial_result_credit_adjustment(task, 3)

    assert adjustment == {
        "expectedResultCount": 4.0,
        "actualResultCount": 3.0,
        "creditAdjustmentApplied": 0.0,
    }
    assert task.credits_used == to_decimal("1.0")
    assert task.extra_metadata == {
        "expectedResultCount": 4,
        "actualResultCount": 3,
        "creditAdjustmentApplied": 0.0,
    }


def test_two_extract_pattern_results_apply_half_credit_adjustment():
    service = ProcessingService()
    task = _build_task(pattern_type="combined", credits_used="1.0")

    adjustment = service._apply_partial_result_credit_adjustment(task, 2)

    assert adjustment == {
        "expectedResultCount": 4.0,
        "actualResultCount": 2.0,
        "creditAdjustmentApplied": 0.5,
    }
    assert task.credits_used == to_decimal("0.5")
    assert task.extra_metadata == {
        "expectedResultCount": 4,
        "actualResultCount": 2,
        "originalCreditsUsed": 1.0,
        "creditAdjustmentReason": "partial_extract_pattern_result",
        "creditAdjustmentApplied": 0.5,
    }


def test_full_extract_pattern_result_keeps_original_credit_charge():
    service = ProcessingService()
    task = _build_task(pattern_type="general_1", num_images=2, credits_used="1.5")

    adjustment = service._apply_partial_result_credit_adjustment(task, 2)

    assert adjustment == {
        "expectedResultCount": 2.0,
        "actualResultCount": 2.0,
        "creditAdjustmentApplied": 0.0,
    }
    assert task.credits_used == to_decimal("1.5")
    assert task.extra_metadata == {
        "expectedResultCount": 2,
        "actualResultCount": 2,
        "creditAdjustmentApplied": 0.0,
    }
