import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.response import Response

from courses.views import (
    create_contest,
    add_contest_to_student,
    fetch_student_contests_in_course,
    fetch_contests,
    get_students_data_in_contests,
)

@pytest.mark.django_db
@patch("courses.views.connection.cursor")
@patch("courses.views.convert_seconds_to_interval", return_value="00:30:00")
def test_create_contest_success(mock_duration, mock_cursor):
    mock_cursor_instance = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
    mock_cursor_instance.fetchone.return_value = [1]  # returning contest ID

    questions = [
        {"questiontext": "What is 2 + 2?", "choices": ["3", "4", "5"], "correctanswerindex": 1}
    ]

    with patch("courses.views.get_course_students_ids", return_value=[101, 102]), \
         patch("courses.views.add_contest_to_student", return_value=True):

        result = create_contest(
            title="Math Contest",
            courseId=1,
            questions=questions,
            quizDuration=1800,
            totalMarks=100,
            passingMarks=50,
            user_id=10,
            discount=0,
            flag=True,
        )
    assert isinstance(result, int)


@pytest.mark.django_db
@patch("courses.views.connection.cursor")
def test_add_contest_to_student_success(mock_cursor):
    mock_cursor_instance = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cursor_instance

    result = add_contest_to_student(studentID=1, contestId=5)
    assert result is True


@pytest.mark.django_db
@patch("courses.views.connection.cursor")
@patch("courses.views.fetch_contests")
def test_fetch_student_contests_in_course_success(mock_fetch, mock_cursor):
    mock_fetch.return_value = [{"contestexamid": 1}]

    mock_cursor_instance = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
    mock_cursor_instance.fetchall.return_value = [(1, 1, True, 95)]
    mock_cursor_instance.description = [
        ("contestexamid",), ("studentid",), ("pass",), ("grade",)
    ]

    contests = fetch_student_contests_in_course(course_id=1, student_id=1)
    assert isinstance(contests, list)
    assert "student" in contests[0]


@pytest.mark.django_db
@patch("courses.views.connection.cursor")
def test_fetch_contests_success(mock_cursor):
    mock_cursor_instance = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cursor_instance

    mock_cursor_instance.fetchall.return_value = [
        (1, 1, 1, "contest", "00:30:00", 100, 50, 0)
    ]
    mock_cursor_instance.description = [
        ("contestexamid",), ("courseid",), ("instructorid",), ("examkind",),
        ("duration",), ("totalmarks",), ("passingmarks",), ("discount",)
    ]

    contests = fetch_contests(course_id=1)
    assert isinstance(contests, list)
    assert contests[0]["examkind"] == "contest"


@pytest.mark.django_db
@patch("courses.views.connection.cursor")
@patch("courses.views.fetch_contests")
@patch("courses.views.get_student_raw_data")
def test_get_students_data_in_contests_success(mock_get_data, mock_fetch, mock_cursor):
    mock_fetch.return_value = [{"contestexamid": 1}]
    mock_get_data.return_value = {"id": 1, "name": "Alice"}

    mock_cursor_instance = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
    mock_cursor_instance.fetchall.return_value = [(1, 1, None, None)]
    mock_cursor_instance.description = [
        ("contestexamid",), ("studentid",), ("pass",), ("grade",)
    ]

    result = get_students_data_in_contests(course_id=1)
    assert isinstance(result, list)
    assert "student" in result[0]

# Fail: Invalid correctanswerindex (out of bounds)
@pytest.mark.django_db
@patch("your_module.connection.cursor")
@patch("your_module.convert_seconds_to_interval", return_value="00:30:00")
def test_create_contest_invalid_correctanswerindex(mock_duration, mock_cursor):
    mock_cursor_instance = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
    mock_cursor_instance.fetchone.return_value = [99]

    questions = [
        {"questiontext": "What is 1 + 1?", "choices": ["1"], "correctanswerindex": 5}  # invalid index
    ]

    result = create_contest(
        title="Invalid Answer Index",
        courseId=1,
        questions=questions,
        quizDuration=1200,
        totalMarks=50,
        passingMarks=30,
        user_id=10,
        discount=5,
        flag=False
    )

    assert isinstance(result, Response)
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid correct answer index" in result.data["error"]


# Fail: DB exception during contest creation
@pytest.mark.django_db
@patch("your_module.connection.cursor")
@patch("your_module.convert_seconds_to_interval", return_value="00:30:00")
def test_create_contest_db_exception(mock_duration, mock_cursor):
    mock_cursor_instance = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cursor_instance

    mock_cursor_instance.execute.side_effect = Exception("DB connection error")

    questions = [
        {"questiontext": "Fail case", "choices": ["A", "B"], "correctanswerindex": 0}
    ]

    result = create_contest(
        title="Error Contest",
        courseId=1,
        questions=questions,
        quizDuration=600,
        totalMarks=10,
        passingMarks=5,
        user_id=1,
        discount=0,
        flag=False
    )

    assert isinstance(result, Response)
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert "DB connection error" in result.data["error"]


# Fail: DB exception during insert into Student_Contest
@pytest.mark.django_db
@patch("your_module.connection.cursor")
def test_add_contest_to_student_exception(mock_cursor):
    mock_cursor_instance = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cursor_instance

    mock_cursor_instance.execute.side_effect = Exception("Insert failed")

    result = add_contest_to_student(studentID=99, contestId=5)

    assert isinstance(result, Response)
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insert failed" in result.data["error"]


# Fail: fetch_contests raises DB error
@pytest.mark.django_db
@patch("your_module.connection.cursor")
def test_fetch_contests_db_failure(mock_cursor):
    mock_cursor_instance = MagicMock()
    mock_cursor.return_value.__enter__.return_value = mock_cursor_instance

    mock_cursor_instance.execute.side_effect = Exception("Query failed")

    result = fetch_contests(course_id=1)
    assert isinstance(result, Response)
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert "Query failed" in result.data["error"]

