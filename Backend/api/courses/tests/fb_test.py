import pytest
from django.db import connection
from courses.views import *
from rest_framework.response import Response
from django.db import transaction
from rest_framework.test import APIRequestFactory
from rest_framework import status
from django.test import RequestFactory
import json
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework.test import force_authenticate
from authenticate import CustomTokenAuthentication


#Test hàm get_review_student_id
@pytest.mark.django_db
def test_get_review_student_id():
    from courses.views import get_review_student_id
    from rest_framework import status

    with connection.cursor() as cursor:
        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'instructor@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo course
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Test Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor_id, category_id))
        course_id = cursor.fetchone()[0]

        # Tạo review
        cursor.execute("""
            INSERT INTO FeedBack_Reviews (StudentID, CourseID, Rating, Review)
            VALUES (%s, %s, 5, 'Great course!')
            RETURNING ReviewID;
        """, (student_id, course_id))
        review_id = cursor.fetchone()[0]

    # Test case 1: Lấy student_id thành công từ review_id hợp lệ
    result = get_review_student_id(review_id)
    assert result == student_id

    # Test case 2: Review_id không tồn tại
    result = get_review_student_id(99999)
    assert isinstance(result, Response)
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in result.data

    # Test case 3: Lỗi khi thực hiện truy vấn
    # Giả lập lỗi bằng cách truyền vào một giá trị không hợp lệ
    result = get_review_student_id('invalid_id')
    assert isinstance(result, Response)
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in result.data


#Test class AddFeedbackReviewToCourseView(APIView)
@pytest.mark.django_db
def test_add_feedback_review_to_course_view():
    client = APIClient()

    # Tạo student, instructor, category, và course trong cơ sở dữ liệu
    with connection.cursor() as cursor:
        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'instructor@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo course
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Test Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor_id, category_id))
        course_id = cursor.fetchone()[0]

    
    # Tạo mock request.user cho CustomTokenAuthentication
   
    client.credentials(
        HTTP_AUTHORIZATION='token_here',  
        HTTP_ROLE='student'  # Quan trọng - đây là điều mà IsStudent kiểm tra
    )

    # Ghi đè authentication cho test - simulate CustomTokenAuthentication
    client.handler._force_user = {'id': student_id, 'role': 'student'}
    client.handler._force_token = 'student'  # Đặt auth là 'student' để IsStudent.has_permission trả về True

    # Test case 1: Thêm review thành công
    response = client.post('/api/auth/add_feedback_to_course', {
        'course_id': course_id,
        'rating': 5,
        'review': 'Great course!'
    }, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Feedback review added successfully'

    # Kiểm tra rating đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("SELECT Rating FROM Course WHERE CourseID = %s", (course_id,))
        assert cursor.fetchone()[0] == 5.0

    # Test case 2: Thiếu các trường bắt buộc
    response = client.post('/api/auth/add_feedback_to_course', {
        'course_id': course_id
    }, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.data

    # Test case 3: Course không tồn tại
    response = client.post('/api/auth/add_feedback_to_course', {
        'course_id': 99999,  # Course không tồn tại
        'rating': 5,
        'review': 'Great course!'
    }, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.data

    # Test case 4: Rating không hợp lệ
    response = client.post('/api/auth/add_feedback_to_course', {
        'course_id': course_id,
        'rating': 6,  # Rating > 5
        'review': 'Great course!'
    }, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.data

#Test class AddFeedbackReviewToInstructorView(APIView)
@pytest.mark.django_db
def test_add_feedback_review_to_instructor_view():
    client = APIClient()

    # Tạo student, instructor, category trong cơ sở dữ liệu
    with connection.cursor() as cursor:
        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'instructor@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

    # Thiết lập authentication và permission
    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='student'
    )

    # Ghi đè authentication cho test - simulate CustomTokenAuthentication
    client.handler._force_user = {'id': student_id, 'role': 'student'}
    client.handler._force_token = 'student'  # Đặt auth là 'student' để IsStudent.has_permission trả về True

    # Test case 1: Thêm review thành công
    response = client.post('/api/auth/add_feedback_to_instructor', {
        'instructor_id': instructor_id,
        'rating': 5,
        'review': 'Great instructor!'
    }, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Feedback review added successfully'

    # Kiểm tra rating đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("SELECT Rating FROM Instructor WHERE InstructorID = %s", (instructor_id,))
        assert cursor.fetchone()[0] == 5.0

    # Test case 2: Thiếu các trường bắt buộc
    response = client.post('/api/auth/add_feedback_to_instructor', {
        'instructor_id': instructor_id
    }, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.data

    # Test case 3: Instructor không tồn tại
    response = client.post('/api/auth/add_feedback_to_instructor', {
        'instructor_id': 99999,  # Instructor không tồn tại
        'rating': 5,
        'review': 'Great instructor!'
    }, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.data

    # Test case 4: Rating không hợp lệ
    response = client.post('/api/auth/add_feedback_to_instructor', {
        'instructor_id': instructor_id,
        'rating': 6,  # Rating > 5
        'review': 'Great instructor!'
    }, format='json')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.data


#Test class EditFeedBackView(APIView)
@pytest.mark.django_db
def test_edit_feedback_view():
    client = APIClient()

    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'instructor@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo course
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Test Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor_id, category_id))
        course_id = cursor.fetchone()[0]

        # Tạo review cho course
        cursor.execute("""
            INSERT INTO FeedBack_Reviews (StudentID, CourseID, Rating, Review)
            VALUES (%s, %s, 4, 'Good course')
            RETURNING ReviewID;
        """, (student_id, course_id))
        course_review_id = cursor.fetchone()[0]

    # Thiết lập authentication và permission
    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='student'
    )
    client.handler._force_user = {'id': student_id, 'role': 'student'}
    client.handler._force_token = 'student'

    # Test case 1: Sửa review thành công cho course
    response = client.put('/api/auth/edit_feedback', {
        'review_id': course_review_id,
        'rating': 5,
        'review': 'Excellent course!',
        'course_id': course_id
    }, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Feedback review added successfully'

    # Kiểm tra rating đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("SELECT Rating FROM Course WHERE CourseID = %s", (course_id,))
        assert cursor.fetchone()[0] == 5.0

    # Test case 2: Thiếu các trường bắt buộc
    response = client.put('/api/auth/edit_feedback', {
        'review_id': course_review_id
    }, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.data

    # Test case 3: Không phải chủ sở hữu review
    # Tạo student khác
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Another Student', 'another@example.com', 'anotherstudent', 'password123')
            RETURNING StudentID;
        """)
        another_student_id = cursor.fetchone()[0]

    # Thiết lập authentication cho student khác
    client.handler._force_user = {'id': another_student_id, 'role': 'student'}
    
    response = client.put('/api/auth/edit_feedback', {
        'review_id': course_review_id,
        'rating': 5,
        'review': 'Excellent course!',
        'course_id': course_id
    }, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'error' in response.data

    # Test case 4: Review không tồn tại
    # Thiết lập lại authentication cho student gốc
    client.handler._force_user = {'id': student_id, 'role': 'student'}
    
    response = client.put('/api/auth/edit_feedback', {
        'review_id': 99999,
        'rating': 5,
        'review': 'Excellent course!',
        'course_id': course_id
    }, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'error' in response.data

#Test class DeleteFeedbackView(APIView)
@pytest.mark.django_db
def test_delete_feedback_view():
    client = APIClient()

    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'instructor@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo course
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Test Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor_id, category_id))
        course_id = cursor.fetchone()[0]

        # Tạo review cho course
        cursor.execute("""
            INSERT INTO FeedBack_Reviews (StudentID, CourseID, Rating, Review)
            VALUES (%s, %s, 4, 'Good course')
            RETURNING ReviewID;
        """, (student_id, course_id))
        review_id = cursor.fetchone()[0]

    # Thiết lập authentication và permission
    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='student'
    )
    client.handler._force_user = {'id': student_id, 'role': 'student'}
    client.handler._force_token = 'student'

    # Test case 1: Xóa review thành công
    response = client.delete(f'/api/auth/delete_feedback/{review_id}')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'FeedBack review deleted successfully'

    # Kiểm tra review đã bị xóa
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM FeedBack_Reviews WHERE ReviewID = %s", (review_id,))
        assert cursor.fetchone()[0] == 0

    # Test case 2: Không phải chủ sở hữu review
    # Tạo review mới
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO FeedBack_Reviews (StudentID, CourseID, Rating, Review)
            VALUES (%s, %s, 4, 'Good course')
            RETURNING ReviewID;
        """, (student_id, course_id))
        review_id = cursor.fetchone()[0]

    # Tạo student khác
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Another Student', 'another@example.com', 'anotherstudent', 'password123')
            RETURNING StudentID;
        """)
        another_student_id = cursor.fetchone()[0]

    # Thiết lập authentication cho student khác
    client.handler._force_user = {'id': another_student_id, 'role': 'student'}
    
    response = client.delete(f'/api/auth/delete_feedback/{review_id}')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'error' in response.data

    # Test case 3: Review không tồn tại
    # Thiết lập lại authentication cho student gốc
    client.handler._force_user = {'id': student_id, 'role': 'student'}
    
    response = client.delete('/api/auth/delete_feedback/99999')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'error' in response.data

#Test class GetFeedBackViewForCourseView(APIView)
@pytest.mark.django_db
def test_get_feedback_for_course_view():
    client = APIClient()

    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'instructor@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo course
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Test Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor_id, category_id))
        course_id = cursor.fetchone()[0]

        # Tạo review cho course
        cursor.execute("""
            INSERT INTO FeedBack_Reviews (StudentID, CourseID, Rating, Review)
            VALUES (%s, %s, 4, 'Good course')
            RETURNING ReviewID;
        """, (student_id, course_id))
        review_id = cursor.fetchone()[0]

    # Thiết lập authentication và permission
    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='student'
    )
    client.handler._force_user = {'id': student_id, 'role': 'student'}
    client.handler._force_token = 'student'

    # Test case 1: Lấy reviews thành công
    response = client.get(f'/api/auth/get_feedbacks_for_course/{course_id}')
    assert response.status_code == status.HTTP_200_OK
    assert 'reviews' in response.data
    assert len(response.data['reviews']) == 1
    assert response.data['reviews'][0]['reviewid'] == review_id
    assert response.data['reviews'][0]['rating'] == 4
    assert response.data['reviews'][0]['review'] == 'Good course'
    assert response.data['reviews'][0]['studentname'] == 'Test Student'

    # Test case 2: Course không có review
    # Tạo course mới không có review
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Empty Course', 'Empty Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor_id, category_id))
        empty_course_id = cursor.fetchone()[0]

    response = client.get(f'/api/auth/get_feedbacks_for_course/{empty_course_id}')
    assert response.status_code == status.HTTP_200_OK
    assert 'reviews' in response.data
    assert len(response.data['reviews']) == 0

    # Test case 3: Course không tồn tại
    response = client.get('/api/auth/get_feedbacks_for_course/99999')
    assert response.status_code == status.HTTP_200_OK
    assert 'reviews' in response.data
    assert len(response.data['reviews']) == 0

#Test class GetFeedBackViewForInstructorView(APIView)
@pytest.mark.django_db
def test_get_feedback_for_instructor_view():
    client = APIClient()

    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'instructor@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo review cho instructor
        cursor.execute("""
            INSERT INTO FeedBack_Reviews (StudentID, InstructorID, Rating, Review)
            VALUES (%s, %s, 4, 'Good instructor')
            RETURNING ReviewID;
        """, (student_id, instructor_id))
        review_id = cursor.fetchone()[0]
        
    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='instructor'
    )
    client.handler._force_user = {'id': instructor_id, 'role': 'instructor'}
    client.handler._force_token = 'instructor'

    # Test case 1: Lấy reviews thành công
    response = client.get(f'/api/auth/get_feedbacks_for_instructor/{instructor_id}')
    assert response.status_code == status.HTTP_200_OK
    assert 'reviews' in response.data
    assert len(response.data['reviews']) == 1
    assert response.data['reviews'][0]['reviewid'] == review_id
    assert response.data['reviews'][0]['rating'] == 4
    assert response.data['reviews'][0]['review'] == 'Good instructor'
    assert response.data['reviews'][0]['studentname'] == 'Test Student'

    # Test case 2: Instructor không có review
    # Tạo instructor mới không có review
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Empty Instructor', 'empty@example.com', 'emptyinstructor', 'password123')
            RETURNING InstructorID;
        """)
        empty_instructor_id = cursor.fetchone()[0]

    response = client.get(f'/api/auth/get_feedbacks_for_instructor/{empty_instructor_id}')
    assert response.status_code == status.HTTP_200_OK
    assert 'reviews' in response.data
    assert len(response.data['reviews']) == 0

    # Test case 3: Instructor không tồn tại
    response = client.get('/api/auth/get_feedbacks_for_instructor/99999')
    assert response.status_code == status.HTTP_200_OK
    assert 'reviews' in response.data
    assert len(response.data['reviews']) == 0

#Test hàm make_student_pay
@pytest.mark.django_db
def test_make_student_pay():
    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo student với balance ban đầu là 1000
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password, Balance)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123', 1000)
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

    # Test case 1: Thanh toán thành công
    amount = 500
    result = make_student_pay(student_id, amount)
    assert result is True

    # Kiểm tra balance đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("SELECT Balance FROM Student WHERE StudentID = %s", (student_id,))
        balance = cursor.fetchone()[0]
        assert balance == 500  # 1000 - 500 = 500

    # Test case 2: Thanh toán số tiền âm
    amount = -100
    result = make_student_pay(student_id, amount)
    assert result is True

    # Kiểm tra balance đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("SELECT Balance FROM Student WHERE StudentID = %s", (student_id,))
        balance = cursor.fetchone()[0]
        assert balance == 600  # 500 - (-100) = 600

    # Test case 3: Thanh toán số tiền bằng 0
    amount = 0
    result = make_student_pay(student_id, amount)
    assert result is True

    # Kiểm tra balance không thay đổi
    with connection.cursor() as cursor:
        cursor.execute("SELECT Balance FROM Student WHERE StudentID = %s", (student_id,))
        balance = cursor.fetchone()[0]
        assert balance == 600  # 600 - 0 = 600

#Test hàm make_transaction
@pytest.mark.django_db
def test_make_transaction():
    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo student với balance ban đầu là 1000
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password, Balance)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123', 1000)
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'instructor@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo course với giá 500
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Test Course', 'Test Description', 500, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor_id, category_id))
        course_id = cursor.fetchone()[0]

    # Test case 1: Thanh toán thành công với discount 20%
    result = make_transaction(student_id, instructor_id, course_id, 20, None)
    assert isinstance(result, int)  # Kiểm tra trả về transaction_id
    assert result > 0

    # Kiểm tra balance đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("SELECT Balance FROM Student WHERE StudentID = %s", (student_id,))
        balance = cursor.fetchone()[0]
        assert balance == 600  # 1000 - (500 * 0.8) = 600

    # Test case 2: Student không đủ tiền
    with connection.cursor() as cursor:
        # Tạo course mới với giá cao hơn balance của student
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Expensive Course', 'Expensive Description', 1000, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor_id, category_id))
        expensive_course_id = cursor.fetchone()[0]

    result = make_transaction(student_id, instructor_id, expensive_course_id, 0, None)
    assert isinstance(result, Response)
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in result.data
    assert result.data['error'] == 'student has no enough balance to enroll on this course'

    # Test case 3: Sử dụng offer
    with connection.cursor() as cursor:
        # Tạo offer
        cursor.execute("""
            INSERT INTO Offer (Discount)
            VALUES (30)
            RETURNING OfferID;
        """)
        offer_id = cursor.fetchone()[0]

        # Tạo course mới
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('New Course', 'New Description', 500, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor_id, category_id))
        new_course_id = cursor.fetchone()[0]

    result = make_transaction(student_id, instructor_id, new_course_id, 0, offer_id)
    assert isinstance(result, int)
    assert result > 0

    # Kiểm tra offer đã bị xóa
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM Offer WHERE OfferID = %s", (offer_id,))
        assert cursor.fetchone()[0] == 0

#Test class GetAppStatsView(APIView)
@pytest.mark.django_db
def test_get_app_stats_view():
    client = APIClient()

    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo 2 students
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Student 1', 'student1@example.com', 'student1', 'password123')
            RETURNING StudentID;
        """)
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Student 2', 'student2@example.com', 'student2', 'password123')
            RETURNING StudentID;
        """)

        # Tạo 2 instructors
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Instructor 1', 'instructor1@example.com', 'instructor1', 'password123')
            RETURNING InstructorID;
        """)
        instructor1_id = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Instructor 2', 'instructor2@example.com', 'instructor2', 'password123')
            RETURNING InstructorID;
        """)
        instructor2_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo 3 courses
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Course 1', 'Description 1', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor1_id, category_id))
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Course 2', 'Description 2', 200, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor1_id, category_id))
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus)
            VALUES ('Course 3', 'Description 3', 300, %s, %s, 'public')
            RETURNING CourseID;
        """, (instructor2_id, category_id))

    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='instructor'
    )
    client.handler._force_user = {'id': instructor1_id, 'role': 'instructor'}
    client.handler._force_token = 'instructor'
    # Ghi đè authentication cho test - simulate CustomTokenAuthentication

    # Test case 1: Lấy thống kê thành công
    response = client.get('/api/auth/get_stats')
    assert response.status_code == status.HTTP_200_OK
    assert 'num_students' in response.data
    assert 'num_instructors' in response.data
    assert 'num_courses' in response.data
    assert response.data['num_students'] == 2
    assert response.data['num_instructors'] == 2
    assert response.data['num_courses'] == 3

    # Test case 2: Không có dữ liệu
    # Xóa tất cả dữ liệu
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM Student")
        cursor.execute("DELETE FROM Instructor")
        cursor.execute("DELETE FROM Course")

    response = client.get('/api/auth/get_stats')
    assert response.status_code == status.HTTP_200_OK
    assert 'num_students' in response.data
    assert 'num_instructors' in response.data
    assert 'num_courses' in response.data
    assert response.data['num_students'] == 0
    assert response.data['num_instructors'] == 0
    assert response.data['num_courses'] == 0

#Test class IncreaseStudentBalanceView(APIView)
@pytest.mark.django_db
def test_increase_student_balance_view():
    client = APIClient()

    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo student với balance ban đầu là 1000
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password, Balance)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123', 1000)
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

    # Thiết lập authentication và permission cho student
    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='student'
    )
    client.handler._force_user = {'id': student_id, 'role': 'student'}
    client.handler._force_token = 'student'

    # Test case 1: Set balance thành công
    amount = 500
    response = client.post(f'/api/auth/increase_student_balance/{amount}')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Balance increased successfully'

    # Kiểm tra balance đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("SELECT Balance FROM Student WHERE StudentID = %s", (student_id,))
        balance = cursor.fetchone()[0]
        assert balance == 500  # Balance được set trực tiếp thành 500

    # Test case 2: Set balance với số tiền âm
    amount = -200
    response = client.post(f'/api/auth/increase_student_balance/{amount}')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Balance increased successfully'

    # Kiểm tra balance đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("SELECT Balance FROM Student WHERE StudentID = %s", (student_id,))
        balance = cursor.fetchone()[0]
        assert balance == -200  # Balance được set trực tiếp thành -200

    # Test case 3: Set balance với số tiền bằng 0
    amount = 0
    response = client.post(f'/api/auth/increase_student_balance/{amount}')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Balance increased successfully'

    # Kiểm tra balance đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("SELECT Balance FROM Student WHERE StudentID = %s", (student_id,))
        balance = cursor.fetchone()[0]
        assert balance == 0  # Balance được set trực tiếp thành 0

    # Test case 4: Không phải student
    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='instructor'
    )
    client.handler._force_user = {'id': student_id, 'role': 'instructor'}
    client.handler._force_token = 'instructor'

    response = client.post(f'/api/auth/increase_student_balance/{amount}')
    assert response.status_code == status.HTTP_403_FORBIDDEN

#Test class GetUserTransactionsView(APIView)
@pytest.mark.django_db
def test_get_user_transactions():
    client = APIClient()

    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'test@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'instructor@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo transaction cho student
        cursor.execute("""
            INSERT INTO Transactions (StudentID, InstructorID)
            VALUES (%s, %s)
            RETURNING TransactionID;
        """, (student_id, instructor_id))
        transaction_id = cursor.fetchone()[0]

    # Test case 1: Lấy giao dịch của student thành công
    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='student'
    )
    client.handler._force_user = {'id': student_id, 'role': 'student'}
    client.handler._force_token = 'student'

    response = client.get('/api/auth/get_transactions')
    assert response.status_code == status.HTTP_200_OK
    assert 'transactions' in response.data
    assert len(response.data['transactions']) == 1
    assert response.data['transactions'][0]['transactionid'] == transaction_id
    assert response.data['transactions'][0]['studentid'] == student_id
    assert response.data['transactions'][0]['instructorid'] == instructor_id
    assert 'student' in response.data['transactions'][0]
    assert 'instructor' in response.data['transactions'][0]

    # Test case 2: Lấy giao dịch của instructor thành công
    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='instructor'
    )
    client.handler._force_user = {'id': instructor_id, 'role': 'instructor'}
    client.handler._force_token = 'instructor'

    response = client.get('/api/auth/get_transactions')
    assert response.status_code == status.HTTP_200_OK
    assert 'transactions' in response.data
    assert len(response.data['transactions']) == 1
    assert response.data['transactions'][0]['transactionid'] == transaction_id
    assert response.data['transactions'][0]['studentid'] == student_id
    assert response.data['transactions'][0]['instructorid'] == instructor_id
    assert 'student' in response.data['transactions'][0]
    assert 'instructor' in response.data['transactions'][0]

    # Test case 3: Không có giao dịch nào
    # Tạo student mới không có giao dịch
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('New Student', 'new@example.com', 'newstudent', 'password123')
            RETURNING StudentID;
        """)
        new_student_id = cursor.fetchone()[0]

    client.credentials(
        HTTP_AUTHORIZATION='token_here',
        HTTP_ROLE='student'
    )
    client.handler._force_user = {'id': new_student_id, 'role': 'student'}
    client.handler._force_token = 'student'

    response = client.get('/api/auth/get_transactions')
    assert response.status_code == status.HTTP_200_OK
    assert 'transactions' in response.data
    assert len(response.data['transactions']) == 0

    # Test case 4: Lỗi khi thực hiện truy vấn
    # Giả lập lỗi bằng cách truyền vào một giá trị không hợp lệ
    client.handler._force_user = {'id': 'invalid_id', 'role': 'student'}
    response = client.get('/api/auth/get_transactions')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.data
