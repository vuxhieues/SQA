import pytest
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch


@pytest.mark.django_db
def test_get_quiz_exam_view_not_found():
    client = APIClient()
    client.force_authenticate(user={"id": 1, "role": "student"})
    response = client.get("/api/auth/get_quiz_exam/9999/")  # Ensure URL path ends with slash
    assert response.status_code == 404
    assert response.data["error"] == "QuizExam not found"


@pytest.mark.django_db
def test_add_quiz_view_valid():
    client = APIClient()
    client.force_authenticate(user={"id": 1, "role": "instructor"})

    data = {
        "title": "Test Quiz",
        "sectionID": 1,
        "questions": [{"question": "Q1", "answer": "A"}],
        "quizDuration": 30,
        "totalMarks": 100,
        "passingMarks": 50
    }

    with patch("courses.views.fetch_top_instructor_by_section", return_value=(1, 10)), \
         patch("courses.views.create_quiz", return_value=5):
        response = client.post("/api/auth/add_quiz", data, format="json")

    assert response.status_code == 200
    assert response.data["message"] == "Quiz Added"


@pytest.mark.django_db
def test_add_quiz_view_missing_fields():
    client = APIClient()
    client.force_authenticate(user={"id": 1, "role": "instructor"})
    response = client.post("/api/auth/add_quiz", {}, format="json")
    assert response.status_code == 400
    assert "smth is missing" in response.data["error"]


@pytest.mark.django_db
def test_update_quiz_view_success():
    client = APIClient()
    client.force_authenticate(user={"id": 1, "role": "instructor"})

    quiz_data = {"quiz": {"id": 1, "title": "Updated Title"}}

    with patch("courses.views.update_quiz", return_value=True):
        response = client.put("/api/auth/update_quiz", quiz_data, format="json")

    assert response.status_code == 200
    assert response.data["message"] == "Quiz succesfully updated"


@pytest.mark.django_db
def test_delete_quiz_view_success():
    client = APIClient()
    client.force_authenticate(user={"id": 1, "role": "instructor"})

    with patch("courses.views.delete_quiz", return_value=True):
        response = client.delete("/api/auth/delete_quiz/5")

    assert response.status_code == 200
    assert response.data["message"] == "Quiz deleted successfully"


@pytest.mark.django_db
def test_submit_quiz_view_success():
    client = APIClient()
    client.force_authenticate(user={"id": 1, "role": "student"})

    payload = {"quizId": 5, "pass": True, "grade": 85}

    with patch("courses.views.connection.cursor") as mock_cursor:
        response = client.post("/api/auth/submit_quiz", payload, format="json")
        assert response.status_code == 200
        assert response.data["message"] == "Quiz submitted successfully"


@pytest.mark.django_db
def test_get_course_quizzes_view_as_instructor():
    client = APIClient()
    client.force_authenticate(user={"id": 1, "role": "instructor"})

    mock_quizzes = [
        {"quizzes": [{"quizexamid": 123}]}
    ]

    with patch("courses.views._fetch_course_quizzes", return_value=mock_quizzes), \
         patch("courses.views.get_student_raw_data", return_value={"id": 2, "name": "Test Student"}), \
         patch("courses.views.connection.cursor") as mock_cursor:

        mock_cursor.return_value.__enter__.return_value.fetchall.return_value = [(2,)]
        mock_cursor.return_value.__enter__.return_value.description = [("studentid",)]

        response = client.get("/api/auth/get_course_quizzes/10")

    assert response.status_code == 200
