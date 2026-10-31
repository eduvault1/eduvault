"""Deterministic performance ranking for EduVault students."""

from collections import defaultdict
from math import isfinite


def _as_float(value, default=0.0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if isfinite(number) else default


def _performance_percent(result):
    """Return a normalized percentage from one stored result."""
    accuracy = _as_float(result.get("accuracy"))
    total_questions = _as_float(result.get("total_questions"))
    score = _as_float(result.get("score"))
    if total_questions > 0:
        return max(0.0, min(100.0, score / total_questions * 100.0))
    return max(0.0, min(100.0, accuracy))


def calculate_rankings(result_rows, current_user_id=None, limit=3):
    """Build the Top 3 from every student's historical result.

    Ranking order is deterministic and performance-based:
    1. Latest normalized percentage, descending.
    2. Previous normalized percentage, descending; students without a previous
       attempt receive 0 for this tie-breaker.
    3. Average normalized percentage across all attempts, descending.
    4. Attempt count, descending.
    5. Username (case-insensitive), then user id, ascending for stable output.

    Results are never deleted or collapsed; every attempt contributes to the
    historical average while only the latest two attempts drive recency ties.
    """
    grouped = defaultdict(list)
    for row in result_rows:
        user_id = row.get("user_id")
        if user_id is not None:
            grouped[user_id].append(dict(row))

    students = []
    for user_id, attempts in grouped.items():
        attempts.sort(key=lambda item: (str(item.get("date_attempted") or ""), int(item.get("id") or 0)), reverse=True)
        performances = [_performance_percent(attempt) for attempt in attempts]
        latest = performances[0]
        previous = performances[1] if len(performances) > 1 else 0.0
        average = sum(performances) / len(performances)
        first = attempts[0]
        students.append({
            "user_id": user_id,
            "username": first.get("username") or "Student",
            "latest_score": round(latest, 2),
            "previous_score": round(previous, 2) if len(performances) > 1 else None,
            "average_score": round(average, 2),
            "attempt_count": len(attempts),
            "latest_attempted": first.get("date_attempted"),
        })

    students.sort(key=lambda student: (
        -student["latest_score"],
        -(student["previous_score"] or 0.0),
        -student["average_score"],
        -student["attempt_count"],
        str(student["username"]).casefold(),
        int(student["user_id"]),
    ))

    for position, student in enumerate(students, start=1):
        student["rank"] = position

    current_student = next(
        (student for student in students if student["user_id"] == current_user_id),
        None,
    )
    return {
        "top_students": students[:limit],
        "current_student": current_student,
        "total_students": len(students),
    }


def calculate_exam_top_performers(result_rows):
    """Return the highest-scoring student for every published exam package."""
    best_by_exam = {}
    for row in result_rows:
        exam_id = row.get("exam_id")
        if exam_id is None:
            continue
        candidate = dict(row)
        candidate["performance"] = round(_performance_percent(candidate), 2)
        current = best_by_exam.get(exam_id)
        if current is None or candidate["performance"] > current["performance"]:
            best_by_exam[exam_id] = candidate

    performers = []
    for exam_id, result in best_by_exam.items():
        performers.append({
            "exam_id": exam_id,
            "exam_title": result.get("exam_title") or "Exam",
            "exam_type": result.get("exam_type") or "mock",
            "student_id": result.get("user_id"),
            "username": result.get("username") or "Student",
            "score": result["performance"],
            "score_raw": result.get("score", 0),
            "total_questions": result.get("total_questions", 0),
            "attempted_at": result.get("date_attempted"),
        })
    return sorted(performers, key=lambda item: (-item["score"], str(item["exam_title"]).casefold()))


def calculate_entrance_top_performers(result_rows, required_subjects=6, limit=3):
    """Rank students by their best scores across the six Entrance subjects."""
    by_student = defaultdict(dict)
    for row in result_rows:
        if row.get("exam_type") != "entrance":
            continue
        user_id = row.get("user_id")
        subject = row.get("subject") or row.get("exam_title") or row.get("exam_id")
        if user_id is None or subject is None:
            continue
        performance = round(_performance_percent(row), 2)
        current = by_student[user_id].get(str(subject))
        if current is None or performance > current["performance"]:
            by_student[user_id][str(subject)] = {
                "performance": performance,
                "row": dict(row),
            }

    leaders = []
    for user_id, subjects in by_student.items():
        if len(subjects) < required_subjects:
            continue
        scores = [item["performance"] for item in subjects.values()]
        first = next(iter(subjects.values()))["row"]
        total_score = round(sum(scores), 2)
        leaders.append({
            "student_id": user_id,
            "student_code": first.get("student_code"),
            "username": first.get("username") or "Student",
            "student_name": first.get("student_name") or first.get("username") or "Student",
            "photo_url": first.get("photo_url"),
            "score": total_score,
            "total_marks": required_subjects * 100,
            "average_score": round(total_score / required_subjects, 2),
            "subjects_completed": len(subjects),
        })

    leaders.sort(key=lambda item: (-item["score"], str(item["username"]).casefold(), int(item["student_id"])))
    for position, leader in enumerate(leaders[:limit], start=1):
        leader["rank"] = position
    return leaders[:limit]


def calculate_mock_top_performers(result_rows, limit=3):
    """Rank students by their highest normalized Mock result, with stable ties."""
    best_by_student = {}
    for row in result_rows:
        if row.get("exam_type") != "mock" or row.get("user_id") is None:
            continue
        candidate = dict(row)
        candidate["performance"] = round(_performance_percent(candidate), 2)
        current = best_by_student.get(candidate["user_id"])
        candidate_order = (candidate["performance"], str(candidate.get("date_attempted") or ""))
        current_order = (current["performance"], str(current.get("date_attempted") or "")) if current else None
        if current is None or candidate_order > current_order:
            best_by_student[candidate["user_id"]] = candidate

    performers = []
    for user_id, result in best_by_student.items():
        performers.append({
            "student_id": user_id,
            "username": result.get("username") or "Student",
            "student_name": result.get("student_name") or result.get("username") or "Student",
            "photo_url": result.get("photo_url"),
            "score": result["performance"],
            "exam_title": result.get("exam_title") or "Mock exam",
            "attempted_at": result.get("date_attempted"),
        })
    performers.sort(key=lambda item: (-item["score"], str(item["student_name"]).casefold(), int(item["student_id"])))
    for position, performer in enumerate(performers[:limit], start=1):
        performer["rank"] = position
    return performers[:limit]
