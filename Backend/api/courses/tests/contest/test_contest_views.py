import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def instructor_token():
    return "instructor_valid_token"

@pytest.fixture
def student_token():
    return "student_valid_token"

@pytest.fixture
def contest_id():
    return 999  # replace with actual ID if available for success tests

@pytest.fixture
def course_id():
    return 1  # replace with valid course ID

@pytest.fixture
def sample_question_ids():
    return [1, 2, 3]  # replace with actual question IDs if needed

# ----------- GET CONTEST EXAM TESTS -----------
@pytest.mark.django_db
def test_get_contest_exam_pass(api_client, instructor_token, contest_id):
    api_client.credentials(HTTP_AUTHORIZATION=instructor_token)
    response = api_client.get(f"/api/contest/{contest_id}/")
    assert response.status_code == 200
    assert "contest" in response.data
    assert "Questions" in response.data

@pytest.mark.django_db
def test_get_contest_exam_fail_not_found(api_client):
    response = api_client.get("/api/contest/123456/")
    assert response.status_code == 404
    assert "error" in response.data

# ----------- MAKE CONTEST TESTS -----------
@pytest.mark.django_db
def test_make_contest_pass(api_client, instructor_token, course_id, sample_question_ids):
    api_client.credentials(HTTP_AUTHORIZATION=instructor_token)
    payload = {
        "title": "Midterm Contest",
        "courseId": course_id,
        "questions": sample_question_ids,
        "quizDuration": 30,
        "totalMarks": 100,
        "discount": 20,
        "passingMarks": 50,
    }
    response = api_client.post("/api/contest/create/", payload, format='json')
    assert response.status_code == 200
    assert response.data["message"] == "Contest succesfully created"

@pytest.mark.django_db
def test_make_contest_fail_missing_fields(api_client, instructor_token):
    api_client.credentials(HTTP_AUTHORIZATION=instructor_token)
    payload = {
        "title": "Missing Fields",
        "courseId": 1
    }
    response = api_client.post("/api/contest/create/", payload, format='json')
    assert response.status_code == 400
    assert "Please provide all required fields" in response.data["message"]

# ----------- DELETE CONTEST TESTS -----------
@pytest.mark.django_db
def test_delete_contest_pass(api_client, instructor_token, contest_id):
    api_client.credentials(HTTP_AUTHORIZATION=instructor_token)
    response = api_client.delete(f"/api/contest/delete/{contest_id}/")
    assert response.status_code == 200
    assert "message" in response.data

@pytest.mark.django_db
def test_delete_contest_fail_invalid(api_client, instructor_token):
    api_client.credentials(HTTP_AUTHORIZATION=instructor_token)
    response = api_client.delete("/api/contest/delete/999999/")
    assert response.status_code == 400 or response.status_code == 404

# ----------- SUBMIT CONTEST TESTS -----------
@pytest.mark.django_db
def test_submit_contest_pass(api_client, student_token, contest_id):
    api_client.credentials(HTTP_AUTHORIZATION=student_token)
    payload = {
        "contestId": contest_id,
        "pass": True,
        "grade": 85,
        "discount": 10
    }
    response = api_client.post("/api/contest/submit/", payload, format='json')
    assert response.status_code == 200
    assert "message" in response.data
    assert "offer" in response.data

@pytest.mark.django_db
def test_submit_contest_fail_missing_fields(api_client, student_token):
    api_client.credentials(HTTP_AUTHORIZATION=student_token)
    payload = {
        "contestId": 1,
        "grade": 90
    }
    response = api_client.post("/api/contest/submit/", payload, format='json')
    assert response.status_code == 400
    assert "error" in response.data

# ----------- GET COURSE CONTESTS TESTS -----------
@pytest.mark.django_db
def test_get_course_contests_pass(api_client, instructor_token, course_id):
    api_client.credentials(HTTP_AUTHORIZATION=instructor_token)
    response = api_client.get(f"/api/course/{course_id}/contests/")
    assert response.status_code == 200
    assert isinstance(response.data, list)

@pytest.mark.django_db
def test_get_course_contests_fail_invalid_course(api_client):
    response = api_client.get("/api/course/9999999/contests/")
    assert response.status_code == 400 or response.status_code == 404
