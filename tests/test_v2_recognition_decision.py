from v2.service import V2AttendanceService


def candidate(student_id: int, score: float, embedding_id: int | None = None, profile_id: int | None = None):
    return {
        "student_id": student_id,
        "student_name": f"Student {student_id}",
        "similarity": score,
        "embedding_id": embedding_id or student_id,
        "profile_id": profile_id or student_id,
    }


def test_strong_unique_match_is_recognized():
    service = V2AttendanceService()

    decision = service._decide_recognition_match(
        candidates=[candidate(1, 0.88), candidate(2, 0.73), candidate(3, 0.60)],
        threshold=0.70,
        margin=0.07,
    )

    assert decision["result"] == "recognized"
    assert decision["best"]["student_id"] == 1


def test_weak_best_match_is_below_threshold():
    service = V2AttendanceService()

    decision = service._decide_recognition_match(
        candidates=[candidate(1, 0.66), candidate(2, 0.61)],
        threshold=0.70,
        margin=0.07,
    )

    assert decision["result"] == "below_threshold"
    assert decision["best"]["student_id"] == 1


def test_close_top_two_matches_are_ambiguous():
    service = V2AttendanceService()

    decision = service._decide_recognition_match(
        candidates=[candidate(1, 0.82), candidate(2, 0.79)],
        threshold=0.70,
        margin=0.07,
    )

    assert decision["result"] == "ambiguous_match"
    assert decision["best"]["student_id"] == 1
    assert decision["second"]["student_id"] == 2


def test_adams_like_face_does_not_match_tan_or_reyes_when_too_close():
    service = V2AttendanceService()

    decision = service._decide_recognition_match(
        candidates=[
            candidate(1, 0.86),  # Adams Jack
            candidate(2, 0.84),  # Tan Theo
            candidate(3, 0.83),  # Reyes Rafael
        ],
        threshold=0.70,
        margin=0.07,
    )

    assert decision["result"] == "ambiguous_match"


def test_adams_like_face_matches_only_adams_when_margin_is_clear():
    service = V2AttendanceService()

    decision = service._decide_recognition_match(
        candidates=[
            candidate(1, 0.91),  # Adams Jack
            candidate(2, 0.72),  # Tan Theo
            candidate(3, 0.70),  # Reyes Rafael
        ],
        threshold=0.70,
        margin=0.07,
    )

    assert decision["result"] == "recognized"
    assert decision["best"]["student_id"] == 1
