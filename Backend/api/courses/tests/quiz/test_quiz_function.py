import pytest
from unittest.mock import patch, MagicMock
from rest_framework.response import Response

# Import your actual functions here
# from courses.views import update_quiz, create_quiz, add_quiz_to_student, fetch_student_quizzes_in_course, fetch_quizzes_overview, get_students_data_in_quizzes

# Mock helpers
def mock_cursor_executes(*args, **kwargs):
    # Simulate database cursor.execute() calls
    return None

def mock_fetchone_returning_quiz_id():
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [123]
    return mock_cursor

def mock_fetchall_quizzes():
    return [
        (1, "Math Quiz", 1, 1, '00:10:00', 100, 50),
        (2, "Science Quiz", 1, 1, '00:15:00', 100, 60)
    ]

def mock_cursor_description_quizexam():
    return [
        ("quizexamid",), ("title",), ("sectionid",), ("instructorid",),
        ("duration",), ("totalmarks",), ("passingmarks",)
    ]

@patch("courses.views.connection.cursor")
def test_update_quiz_success(mock_cursor_context):
    mock_cursor = MagicMock()
    mock_cursor_context.return_value.__enter__.return_value = mock_cursor

    data = {
        "quizID": 1,
        "title": "Updated Quiz",
        "quizDuration": 600,
        "totalMarks": 100,
        "passingMarks": 50,
        "questions": [
            {
                "questiontext": "What is 2+2?",
                "choices": ["1", "2", "3", "4"],
                "correctanswerindex": 3,
                "questionid": 10
            }
        ]
    }
    from courses.views import update_quiz
    result = update_quiz(data)
    assert result is True

@patch("courses.views.connection.cursor")
def test_update_quiz_missing_field(mock_cursor_context):
    data = {
        "title": "Test",
        "quizDuration": 600,
        "totalMarks": 100,
        # missing passingMarks and questions
    }
    from courses.views import update_quiz
    response = update_quiz(data)
    assert isinstance(response, Response)
    assert response.status_code == 400

@patch("courses.views.connection.cursor")
def test_create_quiz_success(mock_cursor_context):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [123]
    mock_cursor_context.return_value.__enter__.return_value = mock_cursor

    data = {
        "title": "New Quiz",
        "sectionID": 1,
        "questions": [
            {
                "questiontext": "What is the capital of France?",
                "choices": ["Paris", "London", "Berlin", "Madrid"],
                "correctanswerindex": 0
            }
        ],
        "quizDuration": 900,
        "totalMarks": 100,
        "passingMarks": 60,
        "user_id": 10,
        "course_id": 1
    }

    from courses.views import create_quiz
    quiz_id = create_quiz(
        data["title"], data["sectionID"], data["questions"],
        data["quizDuration"], data["totalMarks"], data["passingMarks"],
        data["user_id"], data["course_id"], False
    )
    assert quiz_id == 123

@patch("courses.views.connection.cursor")
def test_create_quiz_invalid_correct_answer_index(mock_cursor_context):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [123]
    mock_cursor_context.return_value.__enter__.return_value = mock_cursor

    from courses.views import create_quiz
    result = create_quiz(
        "Test Quiz", 1,
        [{"questiontext": "Q", "choices": ["A"], "correctanswerindex": 5}],
        600, 100, 50, 1, 1, False
    )
    assert isinstance(result, Response)
    assert result.status_code == 400

@patch("courses.views.connection.cursor")
def test_add_quiz_to_student_success(mock_cursor_context):
    mock_cursor = MagicMock()
    mock_cursor_context.return_value.__enter__.return_value = mock_cursor

    from courses.views import add_quiz_to_student
    result = add_quiz_to_student(1, 123)
    assert result is True

@patch("courses.views.connection.cursor")
def test_fetch_student_quizzes_in_course_success(mock_cursor_context):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (123, 1, True, 90)
    ]
    mock_cursor.description = [("quizexamid",), ("studentid",), ("pass",), ("grade",)]
    mock_cursor_context.return_value.__enter__.return_value = mock_cursor

    from courses.views import fetch_student_quizzes_in_course
    sections = [{"coursesectionid": 1}]
    with patch("courses.views.fetch_quizzes_overview", return_value=[
        {"coursesectionid": 1, "quizzes": [{"quizexamid": 123}]}
    ]):
        result = fetch_student_quizzes_in_course(sections, 1)
        assert isinstance(result, list)
        assert "student" in result[0]["quizzes"][0]

@patch("courses.views.connection.cursor")
def test_fetch_quizzes_overview_success(mock_cursor_context):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = mock_fetchall_quizzes()
    mock_cursor.description = mock_cursor_description_quizexam()
    mock_cursor_context.return_value.__enter__.return_value = mock_cursor

    from courses.views import fetch_quizzes_overview
    with patch("courses.views.get_instructor_raw_data", return_value={"id": 1, "name": "Instructor"}):
        sections = [{"coursesectionid": 1}]
        result = fetch_quizzes_overview(sections)
        assert isinstance(result, list)
        assert "quizzes" in result[0]
        assert isinstance(result[0]["quizzes"][0]["instructor"], dict)

@patch("courses.views.connection.cursor")
def test_get_students_data_in_quizzes_success(mock_cursor_context):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (1, 1, True, 80)
    ]
    mock_cursor.description = [("quizexamid",), ("studentid",), ("pass",), ("grade",)]
    mock_cursor_context.return_value.__enter__.return_value = mock_cursor

    from courses.views import get_students_data_in_quizzes
    with patch("courses.views.get_student_raw_data", return_value={"id": 1, "name": "Student"}):
        quizzes = [{"quizexamid": 1}]
        get_students_data_in_quizzes(quizzes)
        assert isinstance(quizzes[0]["student"], list)

@patch("courses.views.connection.cursor")
def test_update_quiz_empty_questions(mock_cursor_context):
    from courses.views import update_quiz
    data = {
        "quizID": 1,
        "title": "No Questions Quiz",
        "quizDuration": 600,
        "totalMarks": 100,
        "passingMarks": 50,
        "questions": []  # Empty questions list
    }
    response = update_quiz(data)
    assert isinstance(response, Response)
    assert response.status_code == 400


@patch("courses.views.connection.cursor")
def test_create_quiz_missing_fields(mock_cursor_context):
    from courses.views import create_quiz
    result = create_quiz(
        title=None,  # Missing title
        sectionID=None,
        questions=[],
        quizDuration=600,
        totalMarks=100,
        passingMarks=50,
        user_id=1,
        course_id=1,
        is_draft=False
    )
    assert isinstance(result, Response)
    assert result.status_code == 400


@patch("courses.views.connection.cursor")
def test_add_quiz_to_student_invalid_input(mock_cursor_context):
    from courses.views import add_quiz_to_student
    result = add_quiz_to_student(None, None)  # Invalid IDs
    assert isinstance(result, Response)
    assert result.status_code == 400


@patch("courses.views.connection.cursor")
def test_fetch_student_quizzes_in_course_empty_sections(mock_cursor_context):
    from courses.views import fetch_student_quizzes_in_course
    result = fetch_student_quizzes_in_course([], 1)  # No sections
    assert isinstance(result, Response)
    assert result.status_code == 400


@patch("courses.views.connection.cursor")
def test_fetch_quizzes_overview_no_data(mock_cursor_context):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = mock_cursor_description_quizexam()
    mock_cursor_context.return_value.__enter__.return_value = mock_cursor

    from courses.views import fetch_quizzes_overview
    with patch("courses.views.get_instructor_raw_data", return_value={"id": 1, "name": "Instructor"}):
        sections = [{"coursesectionid": 1}]
        result = fetch_quizzes_overview(sections)
        assert isinstance(result, list)
        assert len(result[0]["quizzes"]) == 0


@patch("courses.views.connection.cursor")
def test_get_students_data_in_quizzes_empty_quizzes(mock_cursor_context):
    from courses.views import get_students_data_in_quizzes
    result = get_students_data_in_quizzes([])
    assert result == []


