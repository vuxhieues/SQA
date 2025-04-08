import pytest
from django.db import connection
from api.courses.views import update_quiz

@pytest.mark.django_db
def test_update_quiz():
    with connection.cursor() as cursor:
        # Tạo Instructor
        cursor.execute("""
            INSERT INTO Instructor (InstructorName, Email, Username, Password) 
            VALUES ('Test Instructor', 'test@email.com', 'testuser', 'testpassword') RETURNING InstructorID
        """)
        instructor_id = cursor.fetchone()[0]
        print(f"InstructorID: {instructor_id}")  # ✅ In ra InstructorID đã tạo

        # Tạo Course
        cursor.execute("""
            INSERT INTO Course (Title, Description, Price) 
            VALUES ('Sample Course', 'Description here', 100) RETURNING CourseID
        """)
        course_id = cursor.fetchone()[0]
        print(f"CourseID: {course_id}")  # ✅ In ra CourseID đã tạo

        # Tạo CourseSection
        cursor.execute("""
            INSERT INTO CourseSection (CourseID, Title, Duration) 
            VALUES (%s, 'Sample Section', INTERVAL '30 minutes') RETURNING CourseSectionID
        """, [course_id])
        section_id = cursor.fetchone()[0]
        print(f"SectionID: {section_id}")  # ✅ In ra SectionID đã tạo

        # Thêm QuizExam với SectionID hợp lệ
        cursor.execute("""
            INSERT INTO QuizExam (Title, SectionID, InstructorID, Duration, TotalMarks, PassingMarks) 
            VALUES ('Old Title', %s, %s, INTERVAL '1 hour', 50, 25) RETURNING QuizExamID
        """, [section_id, instructor_id])
        quiz_id = cursor.fetchone()[0]
        print(f"QuizID: {quiz_id}")  # ✅ In ra QuizID đã tạo

        # Thêm câu hỏi
        cursor.execute("""
            INSERT INTO Questions (QuizExamID, QuestionText, Choices, CorrectAnswerIndex) 
            VALUES (%s, 'Old Question?', ARRAY[%s, %s, %s, %s], 0) RETURNING QuestionID
        """, [quiz_id, "A", "B", "C", "D"])
        question_id = cursor.fetchone()[0]
        print(f"QuestionID: {question_id}")  # ✅ In ra QuestionID đã tạo

    # Gọi hàm update_quiz()
    quiz_data = {
        "quizID": quiz_id,
        "title": "New Quiz Title",
        "quizDuration": 3600,
        "totalMarks": 100,
        "passingMarks": 50,
        "questions": [
            {"questionid": question_id, "questiontext": "What is 2+2?", "choices": ["1", "2", "3", "4"], "correctanswerindex": 3}
        ]
    }
    
    response = update_quiz(quiz_data)
    print(f"update_quiz() response: {response}")  # ✅ In ra kết quả trả về từ update_quiz()

    assert response is True  

    # Kiểm tra DB
    with connection.cursor() as cursor:
        cursor.execute("SELECT Title, TotalMarks FROM QuizExam WHERE QuizExamID = %s", [quiz_id])
        quiz = cursor.fetchone()
        print(f"Quiz cập nhật: {quiz}")  # ✅ In ra dữ liệu Quiz sau khi cập nhật
        assert quiz[0] == "New Quiz Title"
        assert quiz[1] == 100

        cursor.execute("SELECT QuestionText, Choices FROM Questions WHERE QuestionID = %s", [question_id])
        question = cursor.fetchone()
        print(f"Câu hỏi cập nhật: {question}")  # ✅ In ra dữ liệu Question sau khi cập nhật
        assert question[0] == "What is 2+2?"
        assert question[1] == ["1", "2", "3", "4"]

