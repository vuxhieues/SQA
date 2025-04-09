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

# Test hàm get_course_price
@pytest.mark.django_db
def test_get_course_price():
    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo course với giá 100
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price) 
            VALUES ('Test Course', 'Test Description', 100) RETURNING CourseID
        """)
        course_id = cursor.fetchone()[0]

    # Test case 1: Lấy giá khóa học hợp lệ
    price = get_course_price(course_id)
    assert price == 100.0

    # Test case 2: Lấy giá khóa học không tồn tại
    invalid_price = get_course_price(99999)
    assert isinstance(invalid_price, Response)
    assert invalid_price.status_code == 400
    assert "error" in invalid_price.data

# Test hàm get_instructor_courses
@pytest.mark.django_db
def test_get_instructor_courses():
    with connection.cursor() as cursor:
        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password) 
            VALUES ('Test Instructor', 'test@email.com', 'testuser', 'testpassword') RETURNING InstructorID
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo khóa học 1 - instructor là top instructor
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, SeenStatus) 
            VALUES ('Top Course 1', 'Description 1', 100, %s, 'public') RETURNING CourseID
        """, [instructor_id])
        top_course_id1 = cursor.fetchone()[0]

        # Tạo khóa học 2 - instructor là top instructor (private)
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, SeenStatus) 
            VALUES ('Top Course 2', 'Description 2', 200, %s, 'private') RETURNING CourseID
        """, [instructor_id])
        top_course_id2 = cursor.fetchone()[0]

        # Tạo khóa học 3 - instructor là instructor thường
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, SeenStatus) 
            VALUES ('Normal Course 1', 'Description 3', 300, 'public') RETURNING CourseID
        """)
        normal_course_id1 = cursor.fetchone()[0]

        # Thêm instructor vào khóa học 3
        cursor.execute("""
            INSERT INTO Course_Instructor (CourseID, InstructorID) 
            VALUES (%s, %s)
        """, [normal_course_id1, instructor_id])

    from courses.views import get_instructor_courses

    # Test case 1: Lấy tất cả khóa học (public và private)
    result = get_instructor_courses(instructor_id)
    assert isinstance(result, tuple)
    top_courses, normal_courses = result
    
    # Kiểm tra khóa học top instructor
    assert len(top_courses) == 2
    assert any(course['courseid'] == top_course_id1 for course in top_courses)
    assert any(course['courseid'] == top_course_id2 for course in top_courses)
    
    # Kiểm tra khóa học instructor thường
    assert len(normal_courses) == 1
    assert any(course['courseid'] == normal_course_id1 for course in normal_courses)

    # Test case 2: Chỉ lấy khóa học private
    result = get_instructor_courses(instructor_id, private=True)
    print("Result type:", type(result))
    print("Result data:", result.data if isinstance(result, Response) else result)
    assert isinstance(result, tuple)
    top_courses_private, normal_courses_private = result
    
    # Kiểm tra khóa học top instructor private
    assert len(top_courses_private) == 1
    assert any(course['courseid'] == top_course_id2 for course in top_courses_private)
    
    # Kiểm tra khóa học instructor thường private (không có)
    assert len(normal_courses_private) == 0

    # Test case 3: Instructor không tồn tại
    result = get_instructor_courses(99999)
    assert isinstance(result, Response)
    assert result.status_code == 404
    assert "error" in result.data

# Test hàm get_course_id_from_section_id
@pytest.mark.django_db
def test_get_course_id_from_section_id():
    with connection.cursor() as cursor:
        # Tạo course
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price) 
            VALUES ('Test Course', 'Test Description', 100) RETURNING CourseID
        """)
        course_id = cursor.fetchone()[0]

        # Tạo section cho course
        cursor.execute("""
            INSERT INTO CourseSection (CourseID, Title, Duration) 
            VALUES (%s, 'Test Section', INTERVAL '30 minutes') RETURNING CourseSectionID
        """, [course_id])
        section_id = cursor.fetchone()[0]

    from courses.views import get_course_id_from_section_id

    # Test case 1: Lấy course_id từ section_id hợp lệ
    result = get_course_id_from_section_id(section_id)
    assert result == course_id

    # Test case 2: Lấy course_id từ section_id không tồn tại
    result = get_course_id_from_section_id(99999)
    assert isinstance(result, Response)
    assert result.status_code == 400
    assert "error" in result.data

# Test hàm get_courses_progress
@pytest.mark.django_db
def test_get_courses_progress():
    with connection.cursor() as cursor:
        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password) 
            VALUES ('Test Student', 'test@email.com', 'testuser', 'testpassword') RETURNING StudentID
        """)
        student_id = cursor.fetchone()[0]

        # Tạo course
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, Duration) 
            VALUES ('Test Course', 'Test Description', 100, INTERVAL '2 hours') RETURNING CourseID
        """)
        course_id = cursor.fetchone()[0]

        # Tạo section
        cursor.execute("""
            INSERT INTO CourseSection (CourseID, Title, Duration) 
            VALUES (%s, 'Test Section', INTERVAL '1 hour') RETURNING CourseSectionID
        """, [course_id])
        section_id = cursor.fetchone()[0]

        # Tạo video
        cursor.execute("""
            INSERT INTO Video (CourseSectionID, Title, VideoDuration, VideoLink) 
            VALUES (%s, 'Test Video', INTERVAL '30 minutes', 'https://test-video.com') RETURNING VideoID
        """, [section_id])
        video_id = cursor.fetchone()[0]

        # Thêm thời gian học video
        cursor.execute("""
            INSERT INTO Video_Student (VideoID, StudentID, VideoProgress, CourseID) 
            VALUES (%s, %s, 50.0, %s)
        """, [video_id, student_id, course_id])

    from courses.views import get_courses_progress

    # Test case 1: Tính tiến độ học tập bình thường
    # Thời gian học: 15 phút = 900 giây
    # Tổng thời lượng khóa học: 2 giờ = 7200 giây
    # Tiến độ = 900/7200 = 0.125
    result = get_courses_progress(student_id, course_id)
    assert result == 900/7200  # 15 phút / 2 giờ = 0.125

    # Test case 2: Khóa học không có thời lượng (course_duration = 0)
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE Course SET Duration = INTERVAL '0 minutes' WHERE CourseID = %s
        """, [course_id])
    result = get_courses_progress(student_id, course_id)
    assert result == 900  # Trả về thời gian học (15 phút = 900 giây)

    # Test case 3: Học viên chưa học video nào
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM Video_Student WHERE VideoID = %s AND StudentID = %s
        """, [video_id, student_id])
    result = get_courses_progress(student_id, course_id)
    assert result == 0  # Tiến độ = 0 vì chưa học

    # Test case 4: Khóa học không tồn tại
    with pytest.raises(TypeError):
        get_courses_progress(student_id, 99999)

# Test hàm get_course_duration_by_courseid
@pytest.mark.django_db
def test_get_course_duration_by_courseid():
    with connection.cursor() as cursor:
        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText) 
            VALUES ('Test Category') 
            RETURNING CategoryID
        """)
        category_id = cursor.fetchone()[0]

        # Tạo course với thời lượng 2 giờ (7200 giây) và giá 100
        cursor.execute("""
            INSERT INTO Course (Title, Description, Duration, Price, CategoryID, SeenStatus, Requirements, Certificate) 
            VALUES ('Test Course', 'Test Description', INTERVAL '2 hours', 100, %s, 'public', ARRAY['Test Requirement 1', 'Test Requirement 2'], true) 
            RETURNING CourseID
        """, [category_id])
        course_id = cursor.fetchone()[0]

        # Test case 1: Lấy thời lượng khóa học thành công
        from courses.views import get_course_duration_by_courseid
        duration = get_course_duration_by_courseid(course_id)
        assert duration == 7200  # 2 giờ = 7200 giây

        # Test case 2: Lấy thời lượng khóa học không tồn tại
        duration = get_course_duration_by_courseid(99999)
        assert isinstance(duration, Response)
        assert duration.status_code == 400
        assert "error" in duration.data

        # Test case 3: Lấy thời lượng khóa học với Duration là NULL
        cursor.execute("""
            UPDATE Course SET Duration = INTERVAL '0 minutes' WHERE CourseID = %s
        """, [course_id])
        duration = get_course_duration_by_courseid(course_id)
        assert duration == 0  # Thời lượng 0 phút = 0 giây

        # Cleanup
        cursor.execute("DELETE FROM Course WHERE CourseID = %s", (course_id,))
        cursor.execute("DELETE FROM Categories WHERE CategoryID = %s", (category_id,))

# Test hàm enroll_student_on_course
@pytest.mark.django_db
@pytest.mark.parametrize("test_case", [
    "success",
    "nonexistent",
    "insufficient_balance"
])
def test_enroll_student_on_course(test_case):
    from django.db import transaction
    from django.db import connection
    from courses.views import enroll_student_on_course

    # Tạo dữ liệu test cơ bản
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Tạo student
            cursor.execute("""
                INSERT INTO Student (StudentName, Email, Username, Password, Balance) 
                VALUES ('Test Student', 'test@email.com', 'testuser', 'testpassword', 1000) 
                RETURNING StudentID
            """)
            student_id = cursor.fetchone()[0]

            # Tạo instructor
            cursor.execute("""
                INSERT INTO Instructor (InstructorName, Email, Username, Password) 
                VALUES ('Test Instructor', 'instructor@email.com', 'instructor', 'password') 
                RETURNING InstructorID
            """)
            instructor_id = cursor.fetchone()[0]

            # Tạo category
            cursor.execute("""
                INSERT INTO Categories (CategoryText) 
                VALUES ('Test Category') 
                RETURNING CategoryID
            """)
            category_id = cursor.fetchone()[0]

            # Tạo course
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus, Duration) 
                VALUES ('Test Course', 'Test Description', 100, %s, %s, 'public', INTERVAL '2 hours') 
                RETURNING CourseID
            """, [instructor_id, category_id])
            course_id = cursor.fetchone()[0]

            # Tạo section
            cursor.execute("""
                INSERT INTO CourseSection (CourseID, Title, Duration) 
                VALUES (%s, 'Test Section', INTERVAL '1 hour') 
                RETURNING CourseSectionID
            """, [course_id])
            section_id = cursor.fetchone()[0]

            # Tạo assignment
            cursor.execute("""
                INSERT INTO Assignment (CourseSectionID, Title, Description, MaxMarks, PassingMarks) 
                VALUES (%s, 'Test Assignment', 'Test Description', 100, 50) 
                RETURNING AssignmentID
            """, [section_id])
            assignment_id = cursor.fetchone()[0]

            # Tạo quiz
            cursor.execute("""
                INSERT INTO QuizExam (SectionID, Title, Duration, TotalMarks, PassingMarks, InstructorID) 
                VALUES (%s, 'Test Quiz', INTERVAL '30 minutes', 100, 50, %s) 
                RETURNING QuizExamID
            """, [section_id, instructor_id])
            quiz_id = cursor.fetchone()[0]

            # Tạo contest
            cursor.execute("""
                INSERT INTO ContestExam (CourseID, Title, Duration, TotalMarks, PassingMarks, InstructorID) 
                VALUES (%s, 'Test Contest', INTERVAL '1 hour', 100, 50, %s) 
                RETURNING ContestExamID
            """, [course_id, instructor_id])
            contest_id = cursor.fetchone()[0]
            

    # Test case 1: Học viên tham gia khóa học thành công
    if test_case == "success":
        # Kiểm tra khóa học có tồn tại trước khi đăng ký
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM Course WHERE CourseID = %s
            """, [course_id])
            course_exists = cursor.fetchone()[0]
            assert course_exists == 1, "Course does not exist"

        # Kiểm tra học viên có đủ tiền để đăng ký khóa học
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Balance FROM Student WHERE StudentID = %s
            """, [student_id])
            student_balance = cursor.fetchone()[0]
            assert student_balance >= 100, "Insufficient balance"

        # Thực hiện đăng ký học viên vào khóa học
        response = enroll_student_on_course(student_id, course_id)
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.data["message"] == "Student Enrollment succesfully"

        # Kiểm tra học viên đã được thêm vào khóa học
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM Student_Course 
                WHERE StudentID = %s AND CourseID = %s
            """, [student_id, course_id])
            count = cursor.fetchone()[0]
            assert count == 1

            # Kiểm tra học viên đã được thêm vào assignment
            cursor.execute("""
                SELECT COUNT(*) FROM Student_Assignment 
                WHERE StudentID = %s AND AssignmentID = %s
            """, [student_id, assignment_id])
            count = cursor.fetchone()[0]
            assert count == 1

            # Kiểm tra học viên đã được thêm vào quiz
            cursor.execute("""
                SELECT COUNT(*) FROM Student_Quiz 
                WHERE StudentID = %s AND QuizExamID = %s
            """, [student_id, quiz_id])
            count = cursor.fetchone()[0]
            assert count == 1

            # Kiểm tra học viên đã được thêm vào contest
            cursor.execute("""
                SELECT COUNT(*) FROM Student_Contest 
                WHERE StudentID = %s AND ContestExamID = %s
            """, [student_id, contest_id])
            count = cursor.fetchone()[0]
            assert count == 1

    elif test_case == "nonexistent":
        # Test case 2: Khóa học không tồn tại
        response = enroll_student_on_course(student_id, 99999)
        assert isinstance(response, Response)
        assert response.status_code == 400
        assert "error" in response.data

    elif test_case == "insufficient_balance":
        # Test case 3: Học viên không đủ tiền
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE Student SET Balance = 0 WHERE StudentID = %s
            """, [student_id])
        response = enroll_student_on_course(student_id, course_id)
        assert isinstance(response, Response)
        assert response.status_code == 400
        assert "error" in response.data

# Test class GetInstructorCourses(APIView)
@pytest.mark.django_db
def test_get_instructor_courses_view():
    from django.db import transaction
    from django.db import connection
    from courses.views import GetInstructorCourses
    from rest_framework.test import APIRequestFactory
    from rest_framework import status
    from permission import IsInstructor

    # Tạo dữ liệu test
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Tạo instructor
            cursor.execute("""
                INSERT INTO Instructor (InstructorName, Email, Username, Password) 
                VALUES ('Test Instructor', 'test@email.com', 'testuser', 'testpassword') 
                RETURNING InstructorID
            """)
            instructor_id = cursor.fetchone()[0]

            # Tạo student
            cursor.execute("""
                INSERT INTO Student (StudentName, Email, Username, Password) 
                VALUES ('Test Student', 'student@email.com', 'studentuser', 'studentpassword') 
                RETURNING StudentID
            """)
            student_id = cursor.fetchone()[0]

            # Tạo category
            cursor.execute("""
                INSERT INTO Categories (CategoryText) 
                VALUES ('Test Category') 
                RETURNING CategoryID
            """)
            category_id = cursor.fetchone()[0]

            # Tạo khóa học 1 - instructor là top instructor
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus) 
                VALUES ('Top Course 1', 'Description 1', 100, %s, %s, 'public') 
                RETURNING CourseID
            """, [instructor_id, category_id])
            top_course_id1 = cursor.fetchone()[0]

            # Tạo khóa học 2 - instructor là top instructor (private)
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus) 
                VALUES ('Top Course 2', 'Description 2', 200, %s, %s, 'private') 
                RETURNING CourseID
            """, [instructor_id, category_id])
            top_course_id2 = cursor.fetchone()[0]

            # Tạo khóa học 3 - instructor là instructor thường
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, CategoryID, SeenStatus) 
                VALUES ('Normal Course 1', 'Description 3', 300, %s, 'public') 
                RETURNING CourseID
            """, [category_id])
            normal_course_id1 = cursor.fetchone()[0]

            # Thêm instructor vào khóa học 3
            cursor.execute("""
                INSERT INTO Course_Instructor (CourseID, InstructorID) 
                VALUES (%s, %s)
            """, [normal_course_id1, instructor_id])

    # Tạo request factory
    factory = APIRequestFactory()

    # Test case 1: Lấy danh sách khóa học thành công
    request = factory.get('/api/instructor/courses/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    view = GetInstructorCourses()
    response = view.get(request)

    assert response.status_code == status.HTTP_200_OK
    assert "top_instructor_courses" in response.data
    assert "non_top_instructor_courses" in response.data
    
    # Kiểm tra khóa học top instructor
    top_courses = response.data["top_instructor_courses"]
    assert len(top_courses) == 2
    assert any(course['courseid'] == top_course_id1 for course in top_courses)
    assert any(course['courseid'] == top_course_id2 for course in top_courses)
    
    # Kiểm tra khóa học instructor thường
    normal_courses = response.data["non_top_instructor_courses"]
    assert len(normal_courses) == 1
    assert any(course['courseid'] == normal_course_id1 for course in normal_courses)

    # Test case 2: Instructor không tồn tại
    request = factory.get('/api/instructor/courses/')
    request.user = {'id': 99999, 'role': 'instructor'}
    view = GetInstructorCourses()
    response = view.get(request)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "error" in response.data
    assert response.data["error"] == "Instructor not found"

    # Test case 3: Không có quyền truy cập (không phải là instructor)
    request = factory.get('/api/instructor/courses/')
    request.user = {'id': student_id, 'role': 'student'}
    view = GetInstructorCourses()
    
    # Kiểm tra permission trước khi gọi view
    permission = IsInstructor()
    has_permission = permission.has_permission(request, view)
    assert not has_permission, "Student should not have permission to access instructor courses"
    
    # Gọi view và kiểm tra response
    response = view.get(request)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, dict)
    # Kiểm tra rằng response.data chứa danh sách khóa học rỗng
    assert "top_instructor_courses" in response.data
    assert "non_top_instructor_courses" in response.data
    # Kiểm tra rằng các khóa học trong response là của instructor
    for course in response.data["top_instructor_courses"]:
        assert course['topinstructorid'] == instructor_id
    # Kiểm tra rằng các khóa học trong non_top_instructor_courses có instructor_id trong Course_Instructor
    for course in response.data["non_top_instructor_courses"]:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM Course_Instructor 
                WHERE CourseID = %s AND InstructorID = %s
            """, [course['courseid'], instructor_id])
            count = cursor.fetchone()[0]
            assert count > 0, f"Course {course['courseid']} should have instructor {instructor_id}"

    # Test case 4: User không tồn tại
    request = factory.get('/api/instructor/courses/')
    request.user = None
    view = GetInstructorCourses()
    
    # Kiểm tra xem có ném ra TypeError khi request.user là None
    with pytest.raises(TypeError):
        view.get(request)

# Test class GetStudentCourses(APIView)
@pytest.mark.django_db
def test_get_student_courses_view():
    from django.db import transaction
    from django.db import connection
    from courses.views import GetStudentCourses
    from rest_framework.test import APIRequestFactory
    from rest_framework import status
    from permission import IsStudent

    # Tạo dữ liệu test
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Tạo student
            cursor.execute("""
                INSERT INTO Student (StudentName, Email, Username, Password) 
                VALUES ('Test Student', 'student@email.com', 'studentuser', 'studentpassword') 
                RETURNING StudentID
            """)
            student_id = cursor.fetchone()[0]

            # Tạo instructor
            cursor.execute("""
                INSERT INTO Instructor (InstructorName, Email, Username, Password) 
                VALUES ('Test Instructor', 'test@email.com', 'testuser', 'testpassword') 
                RETURNING InstructorID
            """)
            instructor_id = cursor.fetchone()[0]

            # Tạo category
            cursor.execute("""
                INSERT INTO Categories (CategoryText) 
                VALUES ('Test Category') 
                RETURNING CategoryID
            """)
            category_id = cursor.fetchone()[0]

            # Tạo khóa học 1
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus) 
                VALUES ('Course 1', 'Description 1', 100, %s, %s, 'public') 
                RETURNING CourseID
            """, [instructor_id, category_id])
            course_id1 = cursor.fetchone()[0]

            # Tạo khóa học 2
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus) 
                VALUES ('Course 2', 'Description 2', 200, %s, %s, 'public') 
                RETURNING CourseID
            """, [instructor_id, category_id])
            course_id2 = cursor.fetchone()[0]

            # Thêm student vào khóa học 1 và 2
            cursor.execute("""
                INSERT INTO Student_Course (StudentID, CourseID, PurchaseDate) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, [student_id, course_id1])
            
            cursor.execute("""
                INSERT INTO Student_Course (StudentID, CourseID, PurchaseDate) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, [student_id, course_id2])

    # Tạo request factory
    factory = APIRequestFactory()

    # Test case 1: Lấy danh sách khóa học thành công
    request = factory.get('/api/student/courses/')
    request.user = {'id': student_id, 'role': 'student'}
    view = GetStudentCourses()
    response = view.get(request)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 2
    
    # Kiểm tra thông tin khóa học
    course_ids = [course['courseid'] for course in response.data]
    assert course_id1 in course_ids
    assert course_id2 in course_ids

    # Test case 2: Không có quyền truy cập (không phải là student)
    request = factory.get('/api/student/courses/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    view = GetStudentCourses()
    response = view.get(request)
    
    # Kiểm tra response khi user không phải là student
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    # Kiểm tra rằng response.data chứa danh sách khóa học của instructor
    assert len(response.data) > 0
    # Kiểm tra rằng các khóa học trong response là của instructor
    for course in response.data:
        assert course['topinstructorid'] == instructor_id

    # Test case 3: User không tồn tại
    request = factory.get('/api/student/courses/')
    request.user = None
    view = GetStudentCourses()
    
    # Kiểm tra xem có ném ra TypeError khi request.user là None
    with pytest.raises(TypeError):
        view.get(request)

    # Test case 4: Student không có khóa học nào
    # Tạo student mới không có khóa học
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password) 
            VALUES ('New Student', 'new@email.com', 'newuser', 'newpassword') 
            RETURNING StudentID
        """)
        new_student_id = cursor.fetchone()[0]

    request = factory.get('/api/student/courses/')
    request.user = {'id': new_student_id, 'role': 'student'}
    view = GetStudentCourses()
    response = view.get(request)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 0

# Test class UpdateCourse(APIView)
@pytest.mark.django_db
def test_update_course_view():
    from django.db import transaction
    from django.db import connection
    from courses.views import UpdateCourse
    from rest_framework.test import APIRequestFactory
    from rest_framework import status

    # Tạo dữ liệu test
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Tạo instructor
            cursor.execute("""
                INSERT INTO Instructor (InstructorName, Email, Username, Password)
                VALUES ('Test Instructor', 'test@email.com', 'testuser', 'testpassword')
                RETURNING InstructorID
            """)
            instructor_id = cursor.fetchone()[0]

            # Tạo instructor khác
            cursor.execute("""
                INSERT INTO Instructor (InstructorName, Email, Username, Password)
                VALUES ('Other Instructor', 'other@email.com', 'otheruser', 'otherpassword')
                RETURNING InstructorID
            """)
            other_instructor_id = cursor.fetchone()[0]

            # Tạo category
            cursor.execute("""
                INSERT INTO Categories (CategoryText)
                VALUES ('Test Category')
                RETURNING CategoryID
            """)
            category_id = cursor.fetchone()[0]

            # Tạo khóa học
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus, Duration)
                VALUES ('Test Course', 'Test Description', 100, %s, %s, 'public', INTERVAL '2 hours')
                RETURNING CourseID
            """, [instructor_id, category_id])
            course_id = cursor.fetchone()[0]

            # Tạo section
            cursor.execute("""
                INSERT INTO CourseSection (CourseID, Title, Duration)
                VALUES (%s, 'Test Section', INTERVAL '1 hour')
                RETURNING CourseSectionID
            """, [course_id])
            section_id = cursor.fetchone()[0]

    # Tạo request factory
    factory = APIRequestFactory()

    # Test case 1: Cập nhật khóa học thành công
    request = factory.put('/api/courses/update/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.data = {
        'courseId': course_id,
        'title': 'Updated Course',
        'description': 'Updated Description',
        'categoryID': category_id,
        'seen_status': 'private',
        'price': 200,
        'requirements': ['Requirement 1', 'Requirement 2'],
        'duration': 7200,  # 2 hours in seconds
        'sections': [{
            'sectionId': section_id,
            'title': 'Updated Section'
        }]
    }
    view = UpdateCourse()
    response = view.put(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Course updated successfully'

    # Kiểm tra dữ liệu đã được cập nhật
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Title, Description, Price, SeenStatus, Duration, Requirements
            FROM Course
            WHERE CourseID = %s
        """, [course_id])
        course_data = cursor.fetchone()
        assert course_data[0] == 'Updated Course'
        assert course_data[1] == 'Updated Description'
        assert course_data[2] == 200
        assert course_data[3] == 'private'
        assert str(course_data[4]) == '2:00:00'  # 2 hours in interval format
        assert course_data[5] == ['Requirement 1', 'Requirement 2']

        cursor.execute("""
            SELECT Title, Duration
            FROM CourseSection
            WHERE CourseSectionID = %s
        """, [section_id])
        section_data = cursor.fetchone()
        assert section_data[0] == 'Updated Section'
        assert str(section_data[1]) == '1:00:00'    # 1 hour in interval format

    # Test case 2: Thiếu thông tin bắt buộc
    request = factory.put('/api/courses/update/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.data = {
        'courseId': course_id,
        'title': 'Updated Course'
        # Thiếu các trường bắt buộc khác
    }
    view = UpdateCourse()
    response = view.put(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.data
    assert response.data['error'] == 'Missing required fields'

    # Test case 3: Không phải là top instructor
    request = factory.put('/api/courses/update/')
    request.user = {'id': other_instructor_id, 'role': 'instructor'}
    request.data = {
        'courseId': course_id,
        'title': 'Updated Course',
        'description': 'Updated Description',
        'categoryID': category_id,
        'seen_status': 'private',
        'price': 200,
        'requirements': ['Requirement 1', 'Requirement 2'],
        'duration': 7200,
        'sections': [{
            'sectionId': section_id,
            'title': 'Updated Section'
        }]
    }
    view = UpdateCourse()
    response = view.put(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'error' in response.data
    assert response.data['error'] == 'You are not the top instructor of this course'

    # Test case 4: Khóa học không tồn tại
    request = factory.put('/api/courses/update/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.data = {
        'courseId': 99999,  # ID không tồn tại
        'title': 'Updated Course',
        'description': 'Updated Description',
        'categoryID': category_id,
        'seen_status': 'private',
        'price': 200,
        'requirements': ['Requirement 1', 'Requirement 2'],
        'duration': 7200,
        'sections': [{
            'sectionId': section_id,
            'title': 'Updated Section'
        }]
    }
    view = UpdateCourse()
    response = view.put(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'error' in response.data
    assert response.data['error'] == 'You are not the top instructor of this course'

# Test class GetCourseStatistics(APIView)
@pytest.mark.django_db
def test_get_course_statistics_view():
    from django.db import transaction
    from django.db import connection
    from courses.views import GetCourseStatistics
    from rest_framework.test import APIRequestFactory
    from rest_framework import status

    # Tạo dữ liệu test
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Tạo instructor
            cursor.execute("""
                INSERT INTO Instructor (InstructorName, Email, Username, Password)
                VALUES ('Test Instructor', 'test@email.com', 'testuser', 'testpassword')
                RETURNING InstructorID
            """)
            instructor_id = cursor.fetchone()[0]

            # Tạo instructor khác
            cursor.execute("""
                INSERT INTO Instructor (InstructorName, Email, Username, Password)
                VALUES ('Other Instructor', 'other@email.com', 'otheruser', 'otherpassword')
                RETURNING InstructorID
            """)
            other_instructor_id = cursor.fetchone()[0]

            # Tạo category
            cursor.execute("""
                INSERT INTO Categories (CategoryText)
                VALUES ('Test Category')
                RETURNING CategoryID
            """)
            category_id = cursor.fetchone()[0]

            # Tạo khóa học
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus, Duration)
                VALUES ('Test Course', 'Test Description', 100, %s, %s, 'public', INTERVAL '2 hours')
                RETURNING CourseID
            """, [instructor_id, category_id])
            course_id = cursor.fetchone()[0]

            # Tạo section
            cursor.execute("""
                INSERT INTO CourseSection (CourseID, Title, Duration)
                VALUES (%s, 'Test Section', INTERVAL '1 hour')
                RETURNING CourseSectionID
            """, [course_id])
            section_id = cursor.fetchone()[0]

            # Tạo video
            cursor.execute("""
                INSERT INTO Video (CourseSectionID, Title, VideoDuration, VideoLink)
                VALUES (%s, 'Test Video', INTERVAL '30 minutes', 'https://example.com/video')
                RETURNING VideoID
            """, [section_id])
            video_id = cursor.fetchone()[0]

            # Tạo student
            cursor.execute("""
                INSERT INTO Student (StudentName, Email, Username, Password)
                VALUES ('Test Student', 'student@email.com', 'studentuser', 'studentpassword')
                RETURNING StudentID
            """)
            student_id = cursor.fetchone()[0]

            # Thêm student vào khóa học
            cursor.execute("""
                INSERT INTO Student_Course (StudentID, CourseID, StudentProgress)
                VALUES (%s, %s, 0)
            """, [student_id, course_id])

            # Thêm tiến độ video cho student
            cursor.execute("""
                INSERT INTO Video_Student (VideoID, StudentID, VideoProgress, CourseID)
                VALUES (%s, %s, 50, %s)
            """, [video_id, student_id, course_id])

            # Tạo quiz
            cursor.execute("""
                INSERT INTO QuizExam (SectionID, Title, Duration, TotalMarks, PassingMarks, InstructorID)
                VALUES (%s, 'Test Quiz', INTERVAL '30 minutes', 100, 50, %s)
                RETURNING QuizExamID
            """, [section_id, instructor_id])
            quiz_id = cursor.fetchone()[0]

            # Thêm student vào quiz
            cursor.execute("""
                INSERT INTO Student_Quiz (StudentID, QuizExamID, Grade, Pass)
                VALUES (%s, %s, 80, true)
            """, [student_id, quiz_id])

            # Tạo assignment
            cursor.execute("""
                INSERT INTO Assignment (CourseSectionID, Title, Description, MaxMarks, PassingMarks)
                VALUES (%s, 'Test Assignment', 'Test Description', 100, 50)
                RETURNING AssignmentID
            """, [section_id])
            assignment_id = cursor.fetchone()[0]

            # Thêm student vào assignment
            cursor.execute("""
                INSERT INTO Student_Assignment (StudentID, AssignmentID, Grade, PassFail)
                VALUES (%s, %s, 80, true)
            """, [student_id, assignment_id])

            # Tạo contest
            cursor.execute("""
                INSERT INTO ContestExam (CourseID, Title, Duration, TotalMarks, PassingMarks, InstructorID)
                VALUES (%s, 'Test Contest', INTERVAL '1 hour', 100, 50, %s)
                RETURNING ContestExamID
            """, [course_id, instructor_id])
            contest_id = cursor.fetchone()[0]

            # Thêm student vào contest
            cursor.execute("""
                INSERT INTO Student_Contest (StudentID, ContestExamID, Grade, Pass)
                VALUES (%s, %s, 85, true)
            """, [student_id, contest_id])

    # Tạo request factory
    factory = APIRequestFactory()

    # Test case 1: Lấy thống kê khóa học thành công
    request = factory.get(f'/api/courses/get_course_statistics/{course_id}/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    view = GetCourseStatistics()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_200_OK
    assert 'total_students' in response.data
    assert response.data['total_students'] == 1
    assert 'students_progress' in response.data
    assert len(response.data['students_progress']) == 1
    assert 'assignments' in response.data
    assert 'contests' in response.data
    assert 'quizzes' in response.data
    assert 'sections' in response.data
    assert len(response.data['sections']) == 1
    assert 'videos' in response.data['sections'][0]
    assert len(response.data['sections'][0]['videos']) == 1
    assert 'quarter' in response.data['sections'][0]['videos'][0]
    assert 'half' in response.data['sections'][0]['videos'][0]
    assert 'threequarters' in response.data['sections'][0]['videos'][0]
    assert 'full' in response.data['sections'][0]['videos'][0]

    # Test case 2: Không phải là top instructor
    request = factory.get(f'/api/courses/get_course_statistics/{course_id}/')
    request.user = {'id': other_instructor_id, 'role': 'instructor'}
    view = GetCourseStatistics()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'error' in response.data
    assert response.data['error'] == 'You are not the top instructor of this course'

    # Test case 3: Khóa học không tồn tại
    request = factory.get('/api/courses/get_course_statistics/99999/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    view = GetCourseStatistics()
    response = view.get(request, 99999)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert 'error' in response.data
    assert response.data['error'] == 'You are not the top instructor of this course'

# Test class GetCourseAssignmentsView(APIView)
@pytest.mark.django_db
def test_get_course_assignments_view():
    from django.db import transaction
    from django.db import connection
    from courses.views import GetCourseAssignmentsView
    from rest_framework.test import APIRequestFactory
    from rest_framework import status

    # Tạo dữ liệu test
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Tạo instructor
            cursor.execute("""
                INSERT INTO Instructor (InstructorName, Email, Username, Password)
                VALUES ('Test Instructor', 'test@example.com', 'testuser', 'password123')
                RETURNING InstructorID;
            """)
            instructor_id = cursor.fetchone()[0]

            # Tạo student
            cursor.execute("""
                INSERT INTO Student (StudentName, Email, Username, Password)
                VALUES ('Test Student', 'student@example.com', 'studentuser', 'password123')
                RETURNING StudentID;
            """)
            student_id = cursor.fetchone()[0]

            # Tạo category
            cursor.execute("""
                INSERT INTO Categories (CategoryText)
                VALUES ('Test Category')
                RETURNING CategoryID;
            """)
            category_id = cursor.fetchone()[0]

            # Tạo khóa học
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID)
                VALUES ('Test Course', 'Test Description', 100, %s, %s)
                RETURNING CourseID;
            """, (category_id, instructor_id))
            course_id = cursor.fetchone()[0]

            # Tạo section
            cursor.execute("""
                INSERT INTO CourseSection (CourseID, Title)
                VALUES (%s, 'Test Section')
                RETURNING CourseSectionID;
            """, (course_id,))
            section_id = cursor.fetchone()[0]

            # Tạo assignment
            cursor.execute("""
                INSERT INTO Assignment (CourseSectionID, Title, Description, MaxMarks, PassingMarks)
                VALUES (%s, 'Test Assignment', 'Test Description', 100, 50)
                RETURNING AssignmentID
            """, [section_id])
            assignment_id = cursor.fetchone()[0]

            # Thêm student vào khóa học
            cursor.execute("""
                INSERT INTO Student_Course (StudentID, CourseID, StudentProgress)
                VALUES (%s, %s, 0)
            """, [student_id, course_id])

            # Thêm student vào assignment
            cursor.execute("""
                INSERT INTO Student_Assignment (StudentID, AssignmentID, Grade, PassFail)
                VALUES (%s, %s, 80, true)
            """, [student_id, assignment_id])

    # Tạo request factory
    factory = APIRequestFactory()

    # Test case 1: Lấy danh sách bài tập với quyền instructor
    request = factory.get(f'/api/courses/{course_id}/assignments/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = 'instructor'
    view = GetCourseAssignmentsView()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 1  # Một section
    assert 'assignment' in response.data[0]
    assert len(response.data[0]['assignment']) == 1  # Một assignment
    assert response.data[0]['assignment'][0]['title'] == 'Test Assignment'
    assert response.data[0]['assignment'][0]['description'] == 'Test Description'
    assert response.data[0]['assignment'][0]['maxmarks'] == 100
    assert response.data[0]['assignment'][0]['passingmarks'] == 50
    assert 'data' in response.data[0]['assignment'][0]
    assert len(response.data[0]['assignment'][0]['data']) == 1  # Một student
    assert response.data[0]['assignment'][0]['data'][0]['grade'] == 80
    assert response.data[0]['assignment'][0]['data'][0]['passfail'] == True
    assert 'student' in response.data[0]['assignment'][0]['data'][0]
    assert response.data[0]['assignment'][0]['data'][0]['student']['studentname'] == 'Test Student'
    assert response.data[0]['assignment'][0]['data'][0]['student']['email'] == 'student@example.com'

    # Test case 2: Lấy danh sách bài tập với quyền student
    request = factory.get(f'/api/courses/{course_id}/assignments/')
    request.user = {'id': student_id, 'role': 'student'}
    request.auth = 'student'
    view = GetCourseAssignmentsView()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 1  # Một section
    assert 'assignment' in response.data[0]
    assert len(response.data[0]['assignment']) == 1  # Một assignment
    assert response.data[0]['assignment'][0]['title'] == 'Test Assignment'
    assert response.data[0]['assignment'][0]['description'] == 'Test Description'
    assert response.data[0]['assignment'][0]['maxmarks'] == 100
    assert response.data[0]['assignment'][0]['passingmarks'] == 50
    assert 'student' in response.data[0]['assignment'][0]
    assert response.data[0]['assignment'][0]['student']['grade'] == 80
    assert response.data[0]['assignment'][0]['student']['passfail'] == True

    # Test case 3: Khóa học không tồn tại
    request = factory.get('/api/courses/99999/assignments/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = 'instructor'
    view = GetCourseAssignmentsView()
    response = view.get(request, 99999)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 0  # Khóa học không tồn tại nên trả về danh sách rỗng

    # Test case 4: Assignment không tồn tại
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM Student_Assignment WHERE AssignmentID = %s
        """, [assignment_id])
    
    request = factory.get(f'/api/courses/{course_id}/assignments/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = 'instructor'
    view = GetCourseAssignmentsView()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'error' in response.data
    assert response.data['error'] == 'Assignment not found'

#Test class GetCourseQuizzesView(APIView)
@pytest.mark.django_db
@transaction.atomic
def test_get_course_quizzes_view():
    factory = APIRequestFactory()
    
    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo giảng viên
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'test@example.com', 'testuser', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo học viên
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'student@example.com', 'studentuser', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo danh mục
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo khóa học
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID)
            VALUES ('Test Course', 'Test Description', 100, %s, %s)
            RETURNING CourseID;
        """, (category_id, instructor_id))
        course_id = cursor.fetchone()[0]

        # Tạo section
        cursor.execute("""
            INSERT INTO CourseSection (CourseID, Title)
            VALUES (%s, 'Test Section')
            RETURNING CourseSectionID;
        """, (course_id,))
        section_id = cursor.fetchone()[0]

        # Tạo quiz
        cursor.execute("""
            INSERT INTO QuizExam (Title, SectionID, InstructorID, Duration, TotalMarks, PassingMarks)
            VALUES ('Test Quiz', %s, %s, INTERVAL '30 minutes', 100, 50)
            RETURNING QuizExamID;
        """, (section_id, instructor_id))
        quiz_id = cursor.fetchone()[0]

        # Tạo student quiz
        cursor.execute("""
            INSERT INTO Student_Quiz (StudentID, QuizExamID, Grade, Pass)
            VALUES (%s, %s, 85, true)
        """, (student_id, quiz_id))

    # Test case 1: Lấy danh sách quiz với vai trò giảng viên
    request = factory.get(f'/api/courses/{course_id}/quizzes/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = 'instructor'
    view = GetCourseQuizzesView()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) > 0
    assert 'quizzes' in response.data[0]
    assert len(response.data[0]['quizzes']) > 0
    quiz = response.data[0]['quizzes'][0]
    assert quiz['title'] == 'Test Quiz'
    assert quiz['totalmarks'] == 100
    assert quiz['passingmarks'] == 50
    assert 'data' in quiz
    assert len(quiz['data']) > 0
    assert 'student' in quiz['data'][0]
    assert quiz['data'][0]['student']['studentname'] == 'Test Student'
    assert quiz['data'][0]['grade'] == 85
    assert quiz['data'][0]['pass'] == True

    # Test case 2: Lấy danh sách quiz với vai trò học viên
    request = factory.get(f'/api/courses/{course_id}/quizzes/')
    request.user = {'id': student_id, 'role': 'student'}
    request.auth = 'student'
    view = GetCourseQuizzesView()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) > 0
    assert 'quizzes' in response.data[0]
    assert len(response.data[0]['quizzes']) > 0
    quiz = response.data[0]['quizzes'][0]
    assert quiz['title'] == 'Test Quiz'
    assert quiz['totalmarks'] == 100
    assert quiz['passingmarks'] == 50
    assert 'student' in quiz
    assert quiz['student']['grade'] == 85
    assert quiz['student']['pass'] == True

    # Test case 3: Khóa học không tồn tại
    request = factory.get('/api/courses/99999/quizzes/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = 'instructor'
    view = GetCourseQuizzesView()
    response = view.get(request, 99999)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 0  # Khóa học không tồn tại nên trả về danh sách rỗng

    # Test case 4: Quiz không tồn tại
    with connection.cursor() as cursor:
        # Xóa quiz
        cursor.execute("DELETE FROM Student_Quiz WHERE QuizExamID = %s", (quiz_id,))
        cursor.execute("DELETE FROM QuizExam WHERE QuizExamID = %s", (quiz_id,))

    request = factory.get(f'/api/courses/{course_id}/quizzes/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = 'instructor'
    view = GetCourseQuizzesView()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) > 0
    assert 'quizzes' in response.data[0]
    assert len(response.data[0]['quizzes']) == 0  # Quiz đã bị xóa nên danh sách quiz rỗng

#Test class GetCourseContestsView(APIView)
@pytest.mark.django_db
def test_get_course_contests_view():
    factory = APIRequestFactory()
    
    # Tạo dữ liệu test
    with connection.cursor() as cursor:
        # Tạo giảng viên
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'test@example.com', 'testuser', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo học viên
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'student@example.com', 'studentuser', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo danh mục
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo khóa học
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID)
            VALUES ('Test Course', 'Test Description', 100, %s, %s)
            RETURNING CourseID;
        """, (category_id, instructor_id))
        course_id = cursor.fetchone()[0]

        # Tạo contest
        cursor.execute("""
            INSERT INTO ContestExam (Title, CourseID, InstructorID, Duration, TotalMarks, PassingMarks, Discount)
            VALUES ('Test Contest', %s, %s, INTERVAL '1 hour', 100, 50, 20)
            RETURNING ContestExamID;
        """, (course_id, instructor_id))
        contest_id = cursor.fetchone()[0]

        # Thêm student vào contest
        cursor.execute("""
            INSERT INTO Student_Contest (StudentID, ContestExamID, Grade, Pass)
            VALUES (%s, %s, 85, true)
        """, (student_id, contest_id))

    # Test case 1: Lấy danh sách contest với vai trò giảng viên
    request = factory.get(f'/api/courses/{course_id}/contests/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = 'instructor'
    view = GetCourseContestsView()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) > 0
    contest = response.data[0]
    assert contest['title'] == 'Test Contest'
    assert contest['totalmarks'] == 100
    assert contest['passingmarks'] == 50
    assert contest['discount'] == 20
    assert 'data' in contest
    assert len(contest['data']) > 0
    assert 'student' in contest['data'][0]
    assert contest['data'][0]['student']['studentname'] == 'Test Student'
    assert contest['data'][0]['grade'] == 85
    assert contest['data'][0]['pass'] == True

    # Test case 2: Lấy danh sách contest với vai trò học viên
    request = factory.get(f'/api/courses/{course_id}/contests/')
    request.user = {'id': student_id, 'role': 'student'}
    request.auth = 'student'
    view = GetCourseContestsView()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) > 0
    contest = response.data[0]
    assert contest['title'] == 'Test Contest'
    assert contest['totalmarks'] == 100
    assert contest['passingmarks'] == 50
    assert contest['discount'] == 20
    assert 'student' in contest
    assert contest['student']['grade'] == 85
    assert contest['student']['pass'] == True

    # Test case 3: Khóa học không tồn tại
    request = factory.get('/api/courses/99999/contests/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = 'instructor'
    view = GetCourseContestsView()
    response = view.get(request, 99999)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 0  # Khóa học không tồn tại nên trả về danh sách rỗng

    # Test case 4: Contest không tồn tại
    with connection.cursor() as cursor:
        # Xóa contest
        cursor.execute("DELETE FROM Student_Contest WHERE ContestExamID = %s", (contest_id,))
        cursor.execute("DELETE FROM ContestExam WHERE ContestExamID = %s", (contest_id,))

    request = factory.get(f'/api/courses/{course_id}/contests/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = 'instructor'
    view = GetCourseContestsView()
    response = view.get(request, course_id)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 0  # Contest đã bị xóa nên danh sách rỗng

#Test class StudentEnrollmentView(APIView)
@pytest.mark.django_db
def test_student_enrollment_view():
   
    
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'test@example.com', 'testuser', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password, Balance)
            VALUES ('Test Student', 'student@example.com', 'studentuser', 'password123', 1000)
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID)
            VALUES ('Test Course', 'Test Description', 100, %s, %s)
            RETURNING CourseID;
        """, (category_id, instructor_id))
        course_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO Offer (Discount)
            VALUES (20)
            RETURNING OfferID;
        """)
        offer_id = cursor.fetchone()[0]

    client = APIClient()
    client.force_authenticate(user={'id': student_id, 'role': 'student'})
    url_path = '/api/auth/enroll_student_to_course'

    # Test case 1: Đăng ký thành công với offer và discount tương ứng
    data = {'courseID': course_id, 'offerID': offer_id, 'discount': 20}
    response = client.post(url_path, data, format='json')
    print(f"Test case 1 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Student Enrollment succesfully'

    # Cleanup sau test case 1
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM Student_Course WHERE StudentID = %s AND CourseID = %s
        """, (student_id, course_id))

    # Test case 2: Đăng ký thành công với discount = 0 (không có offer)
    data = {'courseID': course_id, 'discount': 0}
    response = client.post(url_path, data, format='json')
    print(f"Test case 2 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Student Enrollment succesfully'

    

    # Test case 3: Đăng ký thất bại do thiếu courseID
    data = {'discount': 0}
    response = client.post(url_path, data, format='json')
    print(f"Test case 3 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test case 4: Đăng ký thất bại do discount không hợp lệ
    data = {'courseID': course_id, 'discount': 10}
    response = client.post(url_path, data, format='json')
    print(f"Test case 4 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'Invalid discount'

    # Test case 5: Đăng ký thất bại do khóa học không tồn tại
    data = {'courseID': 99999, 'discount': 0}
    response = client.post(url_path, data, format='json')
    print(f"Test case 6 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test case 6: Đăng ký thất bại do không có quyền
    client.force_authenticate(user={'id': instructor_id, 'role': 'instructor'})
    data = {'courseID': course_id, 'discount': 0}
    response = client.post(url_path, data, format='json')
    print(f"Test case 7 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

#Test class StudentEnrollmentPrivateCourseView(APIView)
@pytest.mark.django_db
def test_student_enrollment_in_private_course():
    
    with connection.cursor() as cursor:
        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'test@example.com', 'testuser', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password, Balance)
            VALUES ('Test Student', 'student@example.com', 'studentuser', 'password123', 1000)
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo khóa học private
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Private Course', 'Test Description', 100, %s, %s, 'private')
            RETURNING CourseID;
        """, (category_id, instructor_id))
        private_course_id = cursor.fetchone()[0]

        # Tạo khóa học public
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Public Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (category_id, instructor_id))
        public_course_id = cursor.fetchone()[0]

        # Tạo offer
        cursor.execute("""
            INSERT INTO Offer (Discount)
            VALUES (20)
            RETURNING OfferID;
        """)
        offer_id = cursor.fetchone()[0]

    client = APIClient()
    client.force_authenticate(user={'id': student_id, 'role': 'student'})
    url_path = '/api/auth/enroll_student_to_course'

    # Test case 1: Đăng ký thành công vào khóa học private với offer và discount hợp lệ
    data = {'courseID': private_course_id, 'offerID': offer_id, 'discount': 20, 'is_private': True}
    response = client.post(url_path, data, format='json')
    print(f"Test case 1 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Student Enrollment succesfully'

    # Test case 2: Đăng ký thất bại do học viên đã đăng ký khóa học
    data = {'courseID': private_course_id, 'discount': 0, 'is_private': True}
    response = client.post(url_path, data, format='json')
    print(f"Test case 2 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'student is already enrolled in this course'

    # Test case 3: Đăng ký thất bại do discount không hợp lệ
    # Tạo khóa học private mới để test
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Private Course 2', 'Test Description', 100, %s, %s, 'private')
            RETURNING CourseID;
        """, (category_id, instructor_id))
        private_course_id2 = cursor.fetchone()[0]

    data = {'courseID': private_course_id2, 'offerID': offer_id, 'discount': 0, 'is_private': True}  # Có offerID nhưng discount = 0
    response = client.post(url_path, data, format='json')
    print(f"Test case 3 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'Invalid discount'


    # Test case 4: Đăng ký thất bại do không có quyền truy cập
    # Tạo khóa học private mới để test
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Private Course 3', 'Test Description', 100, %s, %s, 'private')
            RETURNING CourseID;
        """, (category_id, instructor_id))
        private_course_id3 = cursor.fetchone()[0]

    client.force_authenticate(user={'id': instructor_id, 'role': 'instructor'})
    data = {'courseID': private_course_id3, 'discount': 0, 'is_private': True}
    response = client.post(url_path, data, format='json')
    print(f"Test case 5 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

#Test class AddInstructorToCourseView(APIView)
@pytest.mark.django_db
def test_add_instructor_to_course_view():
    from rest_framework.test import APIClient
    
    with connection.cursor() as cursor:
        # Tạo top instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Top Instructor', 'top@example.com', 'topinstructor', 'password123')
            RETURNING InstructorID;
        """)
        top_instructor_id = cursor.fetchone()[0]

        # Tạo instructor khác
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Other Instructor', 'other@example.com', 'otherinstructor', 'password123')
            RETURNING InstructorID;
        """)
        other_instructor_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo khóa học private
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Private Course', 'Test Description', 100, %s, %s, 'private')
            RETURNING CourseID;
        """, (category_id, top_instructor_id))
        private_course_id = cursor.fetchone()[0]

        # Tạo khóa học public
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Public Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (category_id, top_instructor_id))
        public_course_id = cursor.fetchone()[0]

    client = APIClient()
    url_path = '/api/auth/add_instructor_to_course'

    # Test case 1: Thêm instructor thành công vào khóa học private
    client.force_authenticate(user={'id': top_instructor_id, 'role': 'instructor'})
    data = {
        'courseID': private_course_id,
        'instructors': ['otherinstructor']
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 1 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Instructors Added'

    # Test case 2: Thêm instructor thành công vào khóa học public
    data = {
        'courseID': public_course_id,
        'instructors': ['otherinstructor']
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 2 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Instructors Added'

    # Test case 3: Thêm instructor thất bại do không phải là top instructor
    client.force_authenticate(user={'id': other_instructor_id, 'role': 'instructor'})
    data = {
        'courseID': private_course_id,
        'instructors': ['topinstructor']
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 3 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['error'] == 'You are not the top instructor of this course'

    # Test case 4: Thêm instructor thất bại do thiếu thông tin
    client.force_authenticate(user={'id': top_instructor_id, 'role': 'instructor'})
    data = {
        'courseID': private_course_id
        # Thiếu instructors
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 4 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'No instructors selected'

    # Test case 5: Thêm instructor thất bại do không có instructor nào được chọn
    data = {
        'courseID': private_course_id,
        'instructors': []
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 5 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'No instructors selected'

    # Test case 6: Thêm instructor thất bại do instructor không tồn tại
    data = {
        'courseID': private_course_id,
        'instructors': ['nonexistentinstructor']
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 6 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

#Test class MakeAnnouncementView(APIView)
@pytest.mark.django_db
def test_make_announcement_view():
    
    with connection.cursor() as cursor:
        # Tạo top instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Top Instructor', 'top@example.com', 'topinstructor', 'password123')
            RETURNING InstructorID;
        """)
        top_instructor_id = cursor.fetchone()[0]

        # Tạo instructor khác
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Other Instructor', 'other@example.com', 'otherinstructor', 'password123')
            RETURNING InstructorID;
        """)
        other_instructor_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo khóa học private
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Private Course', 'Test Description', 100, %s, %s, 'private')
            RETURNING CourseID;
        """, (category_id, top_instructor_id))
        private_course_id = cursor.fetchone()[0]

        # Tạo khóa học public
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Public Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (category_id, top_instructor_id))
        public_course_id = cursor.fetchone()[0]

        # Thêm instructor khác vào khóa học private
        cursor.execute("""
            INSERT INTO Course_Instructor (CourseID, InstructorID)
            VALUES (%s, %s)
        """, (private_course_id, other_instructor_id))

    client = APIClient()
    url_path = '/api/auth/make_announcement'

    # Test case 1: Tạo announcement thành công bởi top instructor
    client.force_authenticate(user={'id': top_instructor_id, 'role': 'instructor'})
    data = {
        'announcement': 'Test announcement from top instructor',
        'course_id': private_course_id
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 1 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Announcement made successfully'

    # Test case 2: Tạo announcement thành công bởi instructor khác trong khóa học
    client.force_authenticate(user={'id': other_instructor_id, 'role': 'instructor'})
    data = {
        'announcement': 'Test announcement from other instructor',
        'course_id': private_course_id
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 2 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Announcement made successfully'

    # Test case 3: Tạo announcement thất bại do thiếu thông tin
    data = {
        'announcement': 'Test announcement'
        # Thiếu course_id
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 3 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'Missing required fields'

    # Test case 4: Tạo announcement thất bại do không phải là instructor của khóa học
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('New Instructor', 'new@example.com', 'newinstructor', 'password123')
            RETURNING InstructorID;
        """)
        new_instructor_id = cursor.fetchone()[0]

    client.force_authenticate(user={'id': new_instructor_id, 'role': 'instructor'})
    data = {
        'announcement': 'Test announcement from new instructor',
        'course_id': private_course_id
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 4 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'You are not an instructor in this course'

    # Test case 5: Tạo announcement thất bại do khóa học không phải là private
    client.force_authenticate(user={'id': top_instructor_id, 'role': 'instructor'})
    data = {
        'announcement': 'Test announcement for public course',
        'course_id': public_course_id
    }
    response = client.post(url_path, data, format='json')
    print(f"Test case 5 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'Course is not private'

#Test class SearchByTitleView(APIView)
@pytest.mark.django_db
def test_search_by_title_view():
    from rest_framework.test import APIClient
    
    with connection.cursor() as cursor:
        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'test@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo instructor khác
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Other Instructor', 'other@example.com', 'otherinstructor', 'password123')
            RETURNING InstructorID;
        """)
        other_instructor_id = cursor.fetchone()[0]

        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'student@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo khóa học public 1
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Python Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (category_id, instructor_id))
        course_id1 = cursor.fetchone()[0]

        # Tạo khóa học public 2
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Java Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (category_id, other_instructor_id))
        course_id2 = cursor.fetchone()[0]

        # Tạo khóa học public 3
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('JavaScript Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (category_id, other_instructor_id))
        course_id3 = cursor.fetchone()[0]

        # Tạo khóa học private
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Private Course', 'Test Description', 100, %s, %s, 'private')
            RETURNING CourseID;
        """, (category_id, instructor_id))
        private_course_id = cursor.fetchone()[0]

        # Thêm student vào khóa học 1
        cursor.execute("""
            INSERT INTO Student_Course (StudentID, CourseID)
            VALUES (%s, %s)
        """, (student_id, course_id1))

        # Thêm instructor vào khóa học 2
        cursor.execute("""
            INSERT INTO Course_Instructor (CourseID, InstructorID)
            VALUES (%s, %s)
        """, (course_id2, instructor_id))

    client = APIClient()
    url_path = '/api/auth/search_by_title'

    # Test case 1: Tìm kiếm thành công với vai trò student
    client.force_authenticate(user={'id': student_id, 'role': 'student'})
    response = client.get(f"{url_path}?title=Java")
    print(f"Test case 1 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    assert response.data[0]['title'] == 'Java Course'
    assert response.data[0]['instructor']['instructorname'] == 'Other Instructor'

    # Test case 2: Tìm kiếm thành công với vai trò instructor
    client.force_authenticate(user={'id': instructor_id, 'role': 'instructor'})
    response = client.get(f"{url_path}?title=JavaScript")
    print(f"Test case 2 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'JavaScript Course'
    assert response.data[0]['instructor']['instructorname'] == 'Other Instructor'

    # Test case 3: Tìm kiếm thất bại do thiếu title
    response = client.get(url_path)
    print(f"Test case 3 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == 'Please provide all required fields'

    # Test case 4: Tìm kiếm không trả về kết quả
    response = client.get(f"{url_path}?title=NonExistentCourse")
    print(f"Test case 4 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 0

    # Test case 5: Tìm kiếm với vai trò student - không hiển thị khóa học đã đăng ký
    client.force_authenticate(user={'id': student_id, 'role': 'student'})
    response = client.get(f"{url_path}?title=Python")
    print(f"Test case 5 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    # Kiểm tra xem khóa học Python Course có trong kết quả không
    python_course_found = any(course['title'] == 'Python Course' for course in response.data)
    # assert not python_course_found, "Khóa học đã đăng ký không nên xuất hiện trong kết quả tìm kiếm"  
    assert not python_course_found, "Khóa học đã đăng ký không nên xuất hiện trong kết quả tìm kiếm"  


    # Test case 6: Tìm kiếm với vai trò instructor - không hiển thị khóa học đã dạy
    client.force_authenticate(user={'id': instructor_id, 'role': 'instructor'})
    response = client.get(f"{url_path}?title=Java")
    print(f"Test case 6 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    # Kiểm tra xem khóa học Java Course có trong kết quả không
    java_course_found = any(course['title'] == 'Java Course' for course in response.data)
    assert not java_course_found, "Khóa học đã dạy không nên xuất hiện trong kết quả tìm kiếm"

#Test class SearchByTitleView(APIView)
@pytest.mark.django_db
def test_search_by_categories_view():
    from rest_framework.test import APIClient
    
    with connection.cursor() as cursor:
        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'test@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'student@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo category 1
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Programming')
            RETURNING CategoryID;
        """)
        category_id1 = cursor.fetchone()[0]

        # Tạo category 2
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Design')
            RETURNING CategoryID;
        """)
        category_id2 = cursor.fetchone()[0]

        # Tạo khóa học public trong category 1
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Python Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (category_id1, instructor_id))
        course_id1 = cursor.fetchone()[0]

        # Tạo khóa học public trong category 2
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('UI Design Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (category_id2, instructor_id))
        course_id2 = cursor.fetchone()[0]

        # Tạo khóa học private trong category 1
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Private Course', 'Test Description', 100, %s, %s, 'private')
            RETURNING CourseID;
        """, (category_id1, instructor_id))
        private_course_id = cursor.fetchone()[0]

        # Thêm student vào khóa học 1
        cursor.execute("""
            INSERT INTO Student_Course (StudentID, CourseID)
            VALUES (%s, %s)
        """, (student_id, course_id1))

    client = APIClient()
    url_path = '/api/auth/search_by_categories'

    # Test case 1: Tìm kiếm thành công với vai trò student
    client.force_authenticate(user={'id': student_id, 'role': 'student'})
    response = client.get(f"{url_path}?categories={category_id1}")
    print(f"Test case 1 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1  # Chỉ có 1 khóa học public trong category 1
    assert response.data[0][0]['title'] == 'Python Course'
    assert response.data[0][0]['instructor']['instructorname'] == 'Test Instructor'

    # Test case 2: Tìm kiếm thành công với vai trò instructor
    client.force_authenticate(user={'id': instructor_id, 'role': 'instructor'})
    response = client.get(f"{url_path}?categories={category_id2}")
    print(f"Test case 2 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1  # Chỉ có 1 khóa học public trong category 2
    assert response.data[0][0]['title'] == 'UI Design Course'
    assert response.data[0][0]['instructor']['instructorname'] == 'Test Instructor'

    # Test case 3: Tìm kiếm với nhiều categories
    response = client.get(f"{url_path}?categories={category_id1}&categories={category_id2}")
    print(f"Test case 3 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2  # Có 2 danh sách khóa học từ 2 categories
    assert len(response.data[0]) == 1  # Category 1 có 1 khóa học
    assert len(response.data[1]) == 1  # Category 2 có 1 khóa học
    assert response.data[0][0]['title'] == 'Python Course'
    assert response.data[1][0]['title'] == 'UI Design Course'

    # Test case 4: Tìm kiếm với category không tồn tại
    response = client.get(f"{url_path}?categories=99999")
    print(f"Test case 4 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1  # Vẫn trả về 1 danh sách
    assert len(response.data[0]) == 0  # Danh sách rỗng vì không có khóa học

    # Test case 5: Tìm kiếm không có category
    response = client.get(url_path)
    print(f"Test case 5 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 0  # Không có category nào được cung cấp

@pytest.mark.django_db
def test_get_single_course_view():
    with connection.cursor() as cursor:
        # Tạo instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password)
            VALUES ('Test Instructor', 'test@example.com', 'testinstructor', 'password123')
            RETURNING InstructorID;
        """)
        instructor_id = cursor.fetchone()[0]

        # Tạo student
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password)
            VALUES ('Test Student', 'student@example.com', 'teststudent', 'password123')
            RETURNING StudentID;
        """)
        student_id = cursor.fetchone()[0]

        # Tạo category
        cursor.execute("""
            INSERT INTO Categories (CategoryText)
            VALUES ('Test Category')
            RETURNING CategoryID;
        """)
        category_id = cursor.fetchone()[0]

        # Tạo khóa học public
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Public Course', 'Test Description', 100, %s, %s, 'public')
            RETURNING CourseID;
        """, (category_id, instructor_id))
        public_course_id = cursor.fetchone()[0]

        # Tạo khóa học private
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, CategoryID, TopInstructorID, SeenStatus)
            VALUES ('Private Course', 'Test Description', 100, %s, %s, 'private')
            RETURNING CourseID;
        """, (category_id, instructor_id))
        private_course_id = cursor.fetchone()[0]

        # Tạo section cho khóa học public
        cursor.execute("""
            INSERT INTO CourseSection (CourseID, Title, Duration)
            VALUES (%s, 'Test Section', INTERVAL '1 hour')
            RETURNING CourseSectionID;
        """, (public_course_id,))
        section_id = cursor.fetchone()[0]

        # Tạo video cho section
        cursor.execute("""
            INSERT INTO Video (CourseSectionID, Title, VideoDuration, VideoLink)
            VALUES (%s, 'Test Video', INTERVAL '30 minutes', 'https://example.com/video')
            RETURNING VideoID;
        """, (section_id,))
        video_id = cursor.fetchone()[0]

        # Tạo quiz cho section
        cursor.execute("""
            INSERT INTO QuizExam (SectionID, Title, Duration, TotalMarks, PassingMarks, InstructorID)
            VALUES (%s, 'Test Quiz', INTERVAL '30 minutes', 100, 50, %s)
            RETURNING QuizExamID;
        """, (section_id, instructor_id))
        quiz_id = cursor.fetchone()[0]

        # Tạo assignment cho section
        cursor.execute("""
            INSERT INTO Assignment (CourseSectionID, Title, Description, MaxMarks, PassingMarks)
            VALUES (%s, 'Test Assignment', 'Test Description', 100, 50)
            RETURNING AssignmentID;
        """, (section_id,))
        assignment_id = cursor.fetchone()[0]

        # Tạo contest cho khóa học
        cursor.execute("""
            INSERT INTO ContestExam (CourseID, Title, Duration, TotalMarks, PassingMarks, InstructorID)
            VALUES (%s, 'Test Contest', INTERVAL '1 hour', 100, 50, %s)
            RETURNING ContestExamID;
        """, (public_course_id, instructor_id))
        contest_id = cursor.fetchone()[0]

        # Thêm student vào khóa học public
        cursor.execute("""
            INSERT INTO Student_Course (StudentID, CourseID)
            VALUES (%s, %s)
        """, (student_id, public_course_id))

    client = APIClient()
    url_path = '/api/auth/get_single_course'

    # Test case 1: Lấy thông tin khóa học public thành công với vai trò student
    client.force_authenticate(user={'id': student_id, 'role': 'student'})
    response = client.get(f"{url_path}/{public_course_id}", HTTP_AUTHORIZATION='student')
    print(f"Test case 1 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'Public Course'
    assert response.data['topinstructorid'] == instructor_id
    assert len(response.data['sections']) > 0
    assert 'contests' in response.data
    assert isinstance(response.data['contests'], list)
    assert 'assignments' in response.data['sections'][0]
    assert 'videos' in response.data['sections'][0]
    assert len(response.data['sections'][0]['videos']) > 0

    # Test case 2: Lấy thông tin khóa học public thành công với vai trò instructor
    client.force_authenticate(user={'id': instructor_id, 'role': 'instructor'})
    response = client.get(f"{url_path}/{public_course_id}", HTTP_AUTHORIZATION='instructor')
    print(f"Test case 2 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'Public Course'
    assert response.data['topinstructorid'] == instructor_id
    assert len(response.data['sections']) > 0
    assert 'contests' in response.data
    assert isinstance(response.data['contests'], list)
    assert 'assignments' in response.data['sections'][0]
    assert 'videos' in response.data['sections'][0]
    assert len(response.data['sections'][0]['videos']) > 0

    # Test case 3: Khóa học không tồn tại
    response = client.get(f"{url_path}/99999", HTTP_AUTHORIZATION='instructor')
    print(f"Test case 3 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['error'] == 'course not found'

        # Test case 4: Khóa học private với student chưa đăng ký
    client.force_authenticate(user={'id': student_id, 'role': 'student'})
    response = client.get(f"{url_path}/{private_course_id}", HTTP_AUTHORIZATION='student')
    print(f"Test case 4 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'Private Course'
    assert response.data['topinstructorid'] == instructor_id
    assert len(response.data['sections']) == 0  # Khóa học private chưa đăng ký nên không có sections
    assert 'contests' in response.data
    assert isinstance(response.data['contests'], list)
    assert len(response.data['contests']) == 0  # Khóa học private chưa đăng ký nên không có contests

    # Test case 5: Khóa học private với student đã đăng ký
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Student_Course (StudentID, CourseID)
            VALUES (%s, %s)
        """, (student_id, private_course_id))
    
    response = client.get(f"{url_path}/{private_course_id}", HTTP_AUTHORIZATION='student')
    print(f"Test case 5 - Response: {response.status_code}, Data: {response.data}")
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'Private Course'
    assert response.data['topinstructorid'] == instructor_id
#Test hàm get_user_private_courses_view
@pytest.mark.django_db
def test_get_user_private_courses_view():
    from django.db import transaction
    from django.db import connection
    from courses.views import GetUserPrivateCourses
    from rest_framework.test import APIRequestFactory
    from rest_framework import status

    # Tạo dữ liệu test
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Tạo student
            cursor.execute("""
                INSERT INTO Student (StudentName, Email, Username, Password) 
                VALUES ('Test Student', 'student@email.com', 'studentuser', 'studentpassword') 
                RETURNING StudentID
            """)
            student_id = cursor.fetchone()[0]

            # Tạo instructor
            cursor.execute("""
                INSERT INTO Instructor (InstructorName, Email, Username, Password) 
                VALUES ('Test Instructor', 'test@email.com', 'testuser', 'testpassword') 
                RETURNING InstructorID
            """)
            instructor_id = cursor.fetchone()[0]

            # Tạo category
            cursor.execute("""
                INSERT INTO Categories (CategoryText) 
                VALUES ('Test Category') 
                RETURNING CategoryID
            """)
            category_id = cursor.fetchone()[0]

            # Tạo khóa học public cho student
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus) 
                VALUES ('Public Course 1', 'Description 1', 100, %s, %s, 'public') 
                RETURNING CourseID
            """, [instructor_id, category_id])
            public_course_id1 = cursor.fetchone()[0]

            # Tạo khóa học private cho student
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus) 
                VALUES ('Private Course 1', 'Description 2', 200, %s, %s, 'private') 
                RETURNING CourseID
            """, [instructor_id, category_id])
            private_course_id1 = cursor.fetchone()[0]

            # Thêm student vào khóa học public và private
            cursor.execute("""
                INSERT INTO Student_Course (StudentID, CourseID, PurchaseDate) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, [student_id, public_course_id1])
            
            cursor.execute("""
                INSERT INTO Student_Course (StudentID, CourseID, PurchaseDate) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, [student_id, private_course_id1])

            # Tạo khóa học private cho instructor
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus) 
                VALUES ('Private Course 2', 'Description 3', 300, %s, %s, 'private') 
                RETURNING CourseID
            """, [instructor_id, category_id])
            private_course_id2 = cursor.fetchone()[0]

            # Tạo khóa học private cho instructor (không phải top instructor)
            cursor.execute("""
                INSERT INTO Course (Title, Description, Price, CategoryID, SeenStatus) 
                VALUES ('Private Course 3', 'Description 4', 400, %s, 'private') 
                RETURNING CourseID
            """, [category_id])
            private_course_id3 = cursor.fetchone()[0]

            # Thêm instructor vào khóa học private
            cursor.execute("""
                INSERT INTO Course_Instructor (CourseID, InstructorID) 
                VALUES (%s, %s)
            """, [private_course_id3, instructor_id])

    # Tạo request factory
    factory = APIRequestFactory()

    # Test case 1: Student lấy danh sách khóa học private thành công
    request = factory.get('/api/user/private-courses/')
    request.user = {'id': student_id, 'role': 'student'}
    request.auth = "student"
    view = GetUserPrivateCourses()
    response = view.get(request)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 1
    assert response.data[0]['courseid'] == private_course_id1
    assert response.data[0]['seenstatus'] == 'private'

    # Test case 2: Instructor lấy danh sách khóa học private thành công
    request = factory.get('/api/user/private-courses/')
    request.user = {'id': instructor_id, 'role': 'instructor'}
    request.auth = "instructor"
    view = GetUserPrivateCourses()
    response = view.get(request)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, dict)
    assert "top_instructor_courses" in response.data
    assert "non_top_instructor_courses" in response.data
    
    # Kiểm tra rằng có ít nhất một khóa học private trong danh sách
    has_private_course = False
    for course in response.data["top_instructor_courses"]:
        if course['seenstatus'] == 'private':
            has_private_course = True
            break
    assert has_private_course, "Should have at least one private course in top_instructor_courses"
    
    has_private_course = False
    for course in response.data["non_top_instructor_courses"]:
        if course['seenstatus'] == 'private':
            has_private_course = True
            break
    assert has_private_course, "Should have at least one private course in non_top_instructor_courses"

    # Test case 3: Student không có khóa học private nào
    # Tạo student mới không có khóa học
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO Student (StudentName, Email, Username, Password) 
            VALUES ('New Student', 'new@email.com', 'newuser', 'newpassword') 
            RETURNING StudentID
        """)
        new_student_id = cursor.fetchone()[0]

        # Tạo một khóa học private cho student mới
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price, TopInstructorID, CategoryID, SeenStatus) 
            VALUES ('Private Course 4', 'Description 5', 500, %s, %s, 'private') 
            RETURNING CourseID
        """, [instructor_id, category_id])
        private_course_id4 = cursor.fetchone()[0]

        # Thêm student mới vào khóa học private
        cursor.execute("""
            INSERT INTO Student_Course (StudentID, CourseID, PurchaseDate) 
            VALUES (%s, %s, CURRENT_TIMESTAMP)
        """, [new_student_id, private_course_id4])

    request = factory.get('/api/user/private-courses/')
    request.user = {'id': new_student_id, 'role': 'student'}
    request.auth = "student"
    view = GetUserPrivateCourses()
    response = view.get(request)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 1
    assert response.data[0]['courseid'] == private_course_id4
    assert response.data[0]['seenstatus'] == 'private'

    # Test case 4: User không tồn tại
    request = factory.get('/api/user/private-courses/')
    request.user = None
    request.auth = "student"
    view = GetUserPrivateCourses()
    # Kiểm tra xem có ném ra TypeError khi request.user là None
    with pytest.raises(TypeError):
        view.get(request)

    # Test case 5: User không có quyền truy cập (không phải là student hoặc instructor)
    request = factory.get('/api/user/private-courses/')
    request.user = {'id': student_id, 'role': 'student'}
    request.auth = "admin"  # Role không hợp lệ
    view = GetUserPrivateCourses()
    # Kiểm tra xem có ném ra TypeError khi request.auth không phải là student hoặc instructor
    with pytest.raises(TypeError):
        view.get(request)











