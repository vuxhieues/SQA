import pytest
from unittest.mock import patch, MagicMock
from rest_framework.response import Response
from api.courses.views import (
    update_quiz,
    create_quiz,
    add_quiz_to_student,
    fetch_student_quizzes_in_course,
    fetch_quizzes_overview,
    get_students_data_in_quizzes,
)

import django
import os

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.api.settings")
# django.setup()

# Mocks
mock_questions = [
    {
        "questionid": 1,
        "questiontext": "What is 2 + 2?",
        "choices": ["1", "2", "3", "4"],
        "correctanswerindex": 3
    }
]

@patch("api.courses.views.connection")
@patch("api.courses.views.convert_seconds_to_interval", return_value="00:30:00")
def test_update_quiz_success(mock_duration, mock_connection):
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    data = {
        "quizID": 1,
        "title": "Math Quiz",
        "quizDuration": 1800,
        "totalMarks": 100,
        "passingMarks": 50,
        "questions": mock_questions
    }

    response = update_quiz(data)
    assert response is True
    assert mock_cursor.execute.call_count == 2  # 1 for quiz, 1 for question

def test_update_quiz_missing_fields():
    data = {"quizID": 1}
    response = update_quiz(data)
    assert isinstance(response, Response)
    assert response.status_code == 400
    assert "error" in response.data

@patch("api.courses.views.connection")
@patch("api.courses.views.convert_seconds_to_interval", return_value="00:30:00")
def test_create_quiz_success(mock_duration, mock_connection):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [1]  # quizID = 1
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("api.courses.views.get_course_students_ids", return_value=[101, 102]), \
            patch("api.courses.views.add_quiz_to_student", return_value=True):

        quiz_id = create_quiz(
            "Math Quiz", 1, mock_questions, 1800, 100, 50, 999, 10, True
        )
        assert quiz_id == 1

def test_create_quiz_missing_data():
    quiz_id = create_quiz(None, 1, mock_questions, 1800, 100, 50, 999, 10, True)
    assert quiz_id is None

@patch("api.courses.views.connection")
def test_add_quiz_to_student_success(mock_connection):
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    response = add_quiz_to_student(101, 1)
    assert response is True
    mock_cursor.execute.assert_called_once()

@patch("api.courses.views.connection")
@patch("api.courses.views.fetch_quizzes_overview")
def test_fetch_student_quizzes_in_course_success(mock_fetch, mock_connection):
    mock_fetch.return_value = [
        {"quizzes": [{"quizexamid": 1}]}
    ]
    mock_cursor = MagicMock()
    mock_cursor.description = [("QuizExamID",), ("StudentID",), ("Pass",), ("Grade",)]
    mock_cursor.fetchall.return_value = [(1, 101, None, None)]
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    result = fetch_student_quizzes_in_course(mock_fetch.return_value, 101)
    assert isinstance(result, list)
    assert "student" in result[0]["quizzes"][0]

@patch("api.courses.views.connection")
@patch("api.courses.views.get_instructor_raw_data", return_value={"name": "Prof. John"})
def test_fetch_quizzes_overview_success(mock_instructor, mock_connection):
    sections = [{"coursesectionid": 1}]
    mock_cursor = MagicMock()
    mock_cursor.description = [("quizexamid",), ("instructorid",)]
    mock_cursor.fetchall.return_value = [(1, 10)]
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    result = fetch_quizzes_overview(sections)
    assert isinstance(result, list)
    assert "quizzes" in result[0]
    assert result[0]["quizzes"][0]["instructor"]["name"] == "Prof. John"

@patch("api.courses.views.connection")
@patch("api.courses.views.get_student_raw_data", return_value={"name": "Student A"})
def test_get_students_data_in_quizzes(mock_student, mock_connection):
    quizzes = [{"quizexamid": 1}]
    mock_cursor = MagicMock()
    mock_cursor.description = [("QuizExamID",), ("StudentID",)]
    mock_cursor.fetchall.return_value = [(1, 101)]
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    get_students_data_in_quizzes(quizzes)
    assert "student" in quizzes[0]
