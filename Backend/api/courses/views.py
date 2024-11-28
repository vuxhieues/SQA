from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from django.db import connection
import cloudinary.uploader
import base64
import io
from authenticate import GenerateTokens, CustomTokenAuthentication, CustomRefreshAuthentication
from permission import IsInstructor, IsStudent
from datetime import datetime
# Create your views here.

# query = """SELECT CourseID
#     FROM CourseSection AS cs INNER JOIN Course AS c
#     ON cs.CourseID = c.CourseID
#     WHERE cs.CourseSectionID = %s
# """
# try:
#     with connection.cursor() as cursor:
#         cursor.execute(query, (sectionID,))
#         courseID = cursor.fetchone()[0]
# except Exception as e:
#     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#class AskInQAVideoView(APIView):
#     authentication_classes = [CustomTokenAuthentication]
#     permission_classes = [IsStudent]
#     def post(self, request):
#         videoID = request.data.get("videoID", None)
#         question = request.data.get("question", "")
#         if videoID is None or question == "":
#             return Response({"error": "videoID is missing"}, status=status.HTTP_400_BAD_REQUEST)
#         query = """
#             INSERT INTO Messages (MessageText, isAnswer, AnswerTo, SenderStudentID, SenderInstructorID, QAID, ChatID)
#             VALUES (%s, %s, %s, %s, %s, %s, %s);
#         """
#         try:
#             with connection.cursor() as cursor:
#                 cursor.execute("INSERT INTO QA (VideoID) VALUES (%s) RETURNING QAID", (videoID,))
#                 QAID = cursor.fetchone()[0]
#                 cursor.execute(query, (question, False, None, request.user['id'], None, QAID, None))
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         return Response({"message": "Question succesfully asked"}, status=status.HTTP_200_OK)

# cursor.execute("TRUNCATE Assignment RESTART IDENTITY CASCADE")

def decode_base64_to_file(base64_str):
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    file_data = base64.b64decode(base64_str)
    file = io.BytesIO(file_data)
    return file
def convert_seconds_to_interval(seconds):
    if isinstance(seconds, str):
        return seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours} hours {minutes} minutes"
def update_quiz(data):
    quizID = data.get("quizID", None)
    title = data.get("title", None)
    quizDuration = data.get("quizDuration", None)
    totalMarks = data.get("totalMarks", None)
    passingMarks = data.get("passingMarks", None)
    questions = data.get("questions", None)
    if title is None or quizDuration is None or totalMarks is None or passingMarks is None or questions is None:
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
    update_quiz_query = """
        UPDATE QuizExam
        SET Title = %s, Duration = %s, TotalMarks = %s,
        PassingMarks = %s
        WHERE QuizExamID = %s;
    """
    update_quiz_questions_query = """
        UPDATE Questions
        SET QuestionText = %s, Choices = %s, CorrectAnswerIndex = %s
        WHERE QuizExamID = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(update_quiz_query, (title, convert_seconds_to_interval(quizDuration), totalMarks, passingMarks, quizID))
            for question in questions:
                cursor.execute(update_quiz_questions_query, (question['text'], question['choices'],
                    question['correct_answer_index'], quizID))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def update_assignment(data, FILES):
    assignmentID = data.get("assignmentID", None)
    title = data.get("title", None)
    description = data.get("description", None)
    maxMarks = data.get("maxMarks", None)
    passingMarks = data.get("passingMarks", None)
    assignment_file = FILES.get("assignment_file", None)
    if assignmentID is None or title is None or description is None or maxMarks is None or passingMarks is None or assignment_file is None:
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT FileAttched FROM Assignment WHERE AssignmentID = %s", (assignmentID,))
            file_attached = cursor.fetchone()[0]
            new_file_url = file_attached
            try:
                upload_result = cloudinary.uploader.upload(assignment_file, resource_type="raw", public_id=file_attached, overwrite=True)
                new_file_url = upload_result['secure_url']
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)          
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    update_assignment_query = """
        UPDATE Assignment
        SET Title = %s, Description = %s, MaxMarks = %s, PassingMarks = %s, FileAttched = %s
        WHERE AssignmentID = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(update_assignment_query, (title, description, maxMarks, passingMarks, new_file_url, assignmentID))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def update_video(data):
    videoID = data.get("videoID", None)
    video_title = data.get("title", None)
    video = data.get('video', None)
    if videoID is None or video_title is None or video is None:
        return Response({"error": "Video title and video are required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VideoLink FROM Video WHERE VideoID = %s", (videoID,))
            video_attached = cursor.fetchone()[0]
            print("video_attached: ", video_attached)
            new_video_url = video_attached
            try:
                video_file = decode_base64_to_file(video)
                print(video_file)
                upload_result = cloudinary.uploader.upload(video_file, resource_type="video", format='mp4')
                new_video_url = upload_result['secure_url']
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)          
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    print(new_video_url)
    update_video_query = """
        UPDATE Video
        SET title = %s, VideoLink = %s
        WHERE VideoID = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(update_video_query, (video_title, new_video_url, videoID))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def update_section(data, sectionID):
    title = data.get('title', None)
    if title is None:
        return Response({"error": "Title is required"}, status=status.HTTP_400_BAD_REQUEST)
    update_section_query = """
        UPDATE CourseSection
        SET Title = %s
        WHERE CourseSectionID = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(update_section_query, (title, sectionID))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    # Update Quizs #
    quizzes = data.get("quiz", [])
    if len(quizzes) > 0:
        for quiz in quizzes:
            print("quizzes: ", quizzes)
            returned_value = update_quiz(quiz)
            if isinstance(returned_value, Response):
                return returned_value
    print("question")
    # Update Videos #
    videos = data.get("videos", None)
    if videos is not None:
        for video in videos:
            returned_value = update_video(video)
            if returned_value is not True:
                return returned_value
    return True
def create_contest(title, courseId, questions, quizDuration, totalMarks, passingMarks, user_id):
    # check is all data is not None
    if title is None or courseId is None or questions is None or quizDuration is None or totalMarks is None or passingMarks is None or user_id is None:
        return None
    query = """INSERT INTO ContestExam (Title, CourseID, InstructorID, ExamKind, Duration, TotalMarks, PassingMarks)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING ContestExamID;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (title, courseId, user_id, 'contest', convert_seconds_to_interval(quizDuration), totalMarks, passingMarks))
            contestID = cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    query = """
        INSERT INTO Questions (QuizExamID, ContestExamID, QuestionText, Choices, CorrectAnswerIndex)
        VALUES (%s, %s, %s, %s, %s);
    """
    for question in questions:
        try:
            if question['correct_answer_index'] < len(question['choices']):
                with connection.cursor() as cursor:
                    cursor.execute(query, (None, contestID, question['text'], question['choices'], question['correct_answer_index']))
            else:
                return Response({"error": "Invalid correct answer index"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return contestID
def fetch_contests(course_id):
    query = """
        SELECT * FROM ContestExam WHERE CourseID = %s AND ContestExamID NOT IN (
            SELECT ContestExamID FROM InstructorWhiteBoard
        );;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (course_id,))
            contests = cursor.fetchall()
            contests = [dict(zip([desc[0] for desc in cursor.description], contest)) for contest in contests]
            return contests
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def create_quiz(title, sectionID, questions, quizDuration, totalMarks, passingMarks, user_id):
    # check is all data is not None
    if title is None or sectionID is None or questions is None or quizDuration is None or totalMarks is None or passingMarks is None or user_id is None:
        return None
    query = """INSERT INTO QuizExam (Title, SectionID, InstructorID, ExamKind, Duration, TotalMarks, PassingMarks)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING QuizExamID;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (title, sectionID, user_id, 'quiz', convert_seconds_to_interval(quizDuration), totalMarks, passingMarks))
            quizID = cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    query = """
        INSERT INTO Questions (QuizExamID, ContestExamID, QuestionText, Choices, CorrectAnswerIndex)
        VALUES (%s, %s, %s, %s, %s);
    """
    for question in questions:
        try:
            if question['correct_answer_index'] < len(question['choices']):
                with connection.cursor() as cursor:
                    cursor.execute(query, (quizID, None, question['text'], question['choices'], question['correct_answer_index']))
            else:
                return Response({"error": "Invalid correct answer index"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return quizID
    
def create_assignment(title, description, sectionID, maxMarks, passingMarks, assignment_file):
    print(passingMarks)
    query = """
        INSERT INTO Assignment (Title, Description, CourseSectionID, MaxMarks, passingMarks)
        VALUES (%s, %s, %s, %s, %s) RETURNING AssignmentID;
    """
    assignmentID = 0
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (title, description, sectionID, maxMarks, passingMarks))
            assignmentID = cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    if assignment_file is not None:
        try:
            upload_result = cloudinary.uploader.upload(assignment_file, resource_type="raw")
            file_url = upload_result['secure_url']
            query = """
                UPDATE Assignment
                SET FileAttched = %s
                WHERE AssignmentID = %s;
            """ 
            with connection.cursor() as cursor:
                cursor.execute(query, (file_url, assignmentID))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return assignmentID
def add_assignment_to_student(studentID, assignmentID):
    insert_query = """
        INSERT INTO Student_Assignment (StudentID, AssignmentID, SubmissionLink, Grade, SubmissionDate, PassFail)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(insert_query, (studentID, assignmentID, None, 0, None, None))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def fetch_assignments(sections):
    for i, outer_section in enumerate(sections):
        for j, inner_section in enumerate(outer_section):
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM Assignment
                        WHERE CourseSectionID = %s AND AssignmentID NOT IN (
                            SELECT AssignmentID FROM InstructorWhiteBoard
                        );
                    """, (inner_section['coursesectionid'],))
                    section_rows = cursor.fetchall()
                    section_columns = [col[0] for col in cursor.description]
                    sections[i][j]['assignment'] = []
                    sections[i][j]["assignment"] = [dict(zip(section_columns, row)) for row in section_rows]
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
def fetch_videos(sections, student_id):
    for i, outer_section in enumerate(sections):
        for j, inner_section in enumerate(outer_section):
            try:
                with connection.cursor() as cursor:
                    if student_id is not None:
                        cursor.execute("""
                            SELECT v.*, COALESCE(vs.VideoProgress, 0) AS VideoProgress
                            FROM Video AS v LEFT JOIN Video_Student AS vs
                            ON v.VideoID = vs.VideoID AND vs.StudentID = %s
                            WHERE v.CourseSectionID = %s;
                        """, (student_id, inner_section['coursesectionid']))
                    else:
                        cursor.execute("""
                            SELECT * FROM Video
                            WHERE CourseSectionID = %s;
                        """, (inner_section['coursesectionid'],))
                    section_rows = cursor.fetchall()
                    section_columns = [col[0] for col in cursor.description]
                    sections[i][j]['videos'] = []
                    sections[i][j]["videos"] = [dict(zip(section_columns, row)) for row in section_rows]
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
def fetch_quizzes(sections):
    for i, outer_section in enumerate(sections):
        for j, inner_section in enumerate(outer_section):
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM QuizExam
                        WHERE SectionID = %s AND QuizExamID NOT IN (
                            SELECT QuizExamID FROM InstructorWhiteBoard
                        );
                    """, (inner_section['coursesectionid'],))
                    section_rows = cursor.fetchall()
                    section_columns = [col[0] for col in cursor.description]
                    sections[i][j]['quizzes'] = []
                    sections[i][j]['quizzes'].append([dict(zip(section_columns, row)) for row in section_rows])
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
def fetch_courses(query, param, student_id = None):
    courses = []
    if not isinstance(param, tuple):
        param = (param,)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, param)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            courses = [dict(zip(columns, row)) for row in rows]
            course_ids = [course['courseid'] for course in courses]
            sections = []
            contests = []
            for i, course_id in enumerate(course_ids):
                if student_id is not None:
                    returned_value = get_last_watched_video_course(student_id)
                    if isinstance(returned_value, Response):
                        return returned_value
                    courses[i]['last_watched_video'] = returned_value
                cursor.execute("""
                    SELECT * FROM CourseSection
                    WHERE courseid = %s;
                """, (course_id,))
                section_rows = cursor.fetchall()
                section_columns = [col[0] for col in cursor.description]
                sections.append([dict(zip(section_columns, row)) for row in section_rows])
                contests.append(fetch_contests(course_id))
            #////////////////////////////////////////Fetch Contests/////////////////////////////////////////#
            if isinstance(contests, Response):
                return contests
            #////////////////////////////////////////Fetch Quizzes/////////////////////////////////////////#
            sections = fetch_quizzes(sections)
            if isinstance(sections, Response):
                return sections
            #////////////////////////////////////////Fetch Videos/////////////////////////////////////////#
            sections = fetch_videos(sections, student_id)
            if isinstance(sections, Response):
                return sections
            #////////////////////////////////////////Fetch Assignment/////////////////////////////////////////#
            sections = fetch_assignments(sections)
            if isinstance(sections, Response):
                return sections
            data = []
            for i in range(len(courses)):
                temp_data = {}
                temp_data = courses[i]
                temp_data['contests'] = contests[i]
                temp_data['sections'] = sections[i]
                data.append(temp_data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return data
def add_sections(sections, course_id, user_id):
    quiz_messages = []
    sectionIDs = []
    for section in sections:
        section_title = section.get("title", None)
        section_videos = section.get("videos", [])
        section_quizzes = section.get("quizzes", [])
        if section_title is None:
            return Response({"error": "Section title is required"}, status=status.HTTP_400_BAD_REQUEST)
        create_section_query = """
            INSERT INTO coursesection (courseid, title)
            VALUES (%s, %s) RETURNING CourseSectionID;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(create_section_query, (course_id, section_title))
                section_id = cursor.fetchone()[0]
                sectionIDs.append(section_id)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        for quiz in section_quizzes:
            returned_value = create_quiz(title=quiz.get('title', None), sectionID=section_id, questions=quiz.get('questions', None),
                quizDuration=quiz.get('quizDuration', None), totalMarks=quiz.get('totalMarks', None), passingMarks=quiz.get('passingMarks', None),
                user_id=user_id)
            if isinstance(returned_value, Response):
                quiz_messages.append(returned_value.data)
        for video in section_videos:
            video_title = video.get("title", None)
            video = video.get('video', None)
            if video is not None:
                try:
                    video_file = decode_base64_to_file(video)
                    upload_result = cloudinary.uploader.upload(video_file, resource_type='video', format='mp4')
                    video_url = upload_result['secure_url']
                    create_video_query = """
                        INSERT INTO video (coursesectionid, title, videolink)
                        VALUES (%s, %s, %s);
                    """
                    with connection.cursor() as cursor:
                        cursor.execute(create_video_query, (section_id, video_title, video_url))
                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "error": f"Video in section is missing"
                }, status=status.HTTP_400_BAD_REQUEST) 
    return (sectionIDs, quiz_messages) 
def fetch_top_instructor_by_section(section_id):
    try:
        query = """
            SELECT c.TopInstructorID, c.CourseID
            FROM Course AS c INNER JOIN CourseSection AS cs
            ON c.CourseID = cs.courseid
            WHERE cs.CourseSectionId = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, (section_id,))
            result = cursor.fetchone()
            if result:
                top_instructor_id, course_id = result
                return (top_instructor_id, course_id)
            else:
                return (None, None)
    except Exception as e:
        return (Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST), False)
def fetch_top_instructor_by_course(course_id):
    try:
        query = """
            SELECT TopInstructorID
            FROM Course
            WHERE CourseId = %s
        """
        with connection.cursor() as cursor:
            print(course_id)
            cursor.execute(query, (course_id,))
            result = cursor.fetchone()[0]
            print("result: ", result)
            if result:
                top_instructor_id = result
                print(top_instructor_id)
                return (top_instructor_id, course_id)
            else:
                return (None, None)
    except Exception as e:
        return (Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST), False)

def fetch_assignment_for_whiteboard(whiteboard_items):
    for whiteboard_item in whiteboard_items:
        if whiteboard_item['assignmentid'] is not None:
            query = """
                SELECT * FROM Assignment WHERE AssignmentID = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (whiteboard_item['assignmentid'],))
                row = cursor.fetchone()
                columns = [col[0] for col in cursor.description]
                if row:
                    del whiteboard_item['assignmentid'] 
                    whiteboard_item['assignment'] = dict(zip(columns, row))
                    break
def fetch_instructor_for_whiteboard(whiteboard_items):
    for whiteboard_item in whiteboard_items:
        if whiteboard_item['instructorid'] is not None:
            query = """
                SELECT * FROM Instructor WHERE InstructorId = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (whiteboard_item['instructorid'],))
                row = cursor.fetchone()
                columns = [col[0] for col in cursor.description]
                if row:
                    del whiteboard_item['instructorid'] 
                    whiteboard_item['instructor'] = dict(zip(columns, row))
                    break
def fetch_quiz_for_whiteboard(whiteboard_items):
    for whiteboard_item in whiteboard_items:
        if whiteboard_item['quizexamid'] is not None:
            query = """
                SELECT * FROM QuizExam WHERE QuizExamId = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (whiteboard_item['quizexamid'],))
                row = cursor.fetchone()
                columns = [col[0] for col in cursor.description]
                if row:
                    del whiteboard_item['quizexamid'] 
                    whiteboard_item['quiz'] = dict(zip(columns, row))
                    break
def fetch_contest_for_whiteboard(whiteboard_items):
    for whiteboard_item in whiteboard_items:
        if whiteboard_item['contestexamid'] is not None:
            query = """
                SELECT * FROM ContestExam WHERE ContestExamId = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (whiteboard_item['contestexamid'],))
                row = cursor.fetchone()
                columns = [col[0] for col in cursor.description]
                if row:
                    del whiteboard_item['contestexamid']
                    whiteboard_item['contest'] = dict(zip(columns, row))
                    break
def fetch_whiteboard(course_id):
    query = """
        SELECT wb.*
        FROM InstructorWhiteBoard AS wb
        INNER JOIN Course AS c
        ON wb.CourseID = c.CourseID
        WHERE c.CourseID = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (course_id,))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            whiteboard_items = [dict(zip(columns, row)) for row in rows]
            fetch_assignment_for_whiteboard(whiteboard_items)
            fetch_contest_for_whiteboard(whiteboard_items)
            fetch_instructor_for_whiteboard(whiteboard_items)
            fetch_quiz_for_whiteboard(whiteboard_items)
            return whiteboard_items
    except Exception as e:
        return (Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST))

def get_course_price(course_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Price FROM Course WHERE CourseID = %s", (course_id,))
            print("get_course_price")
            return cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def get_student_current_balance(student_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Balance FROM Student WHERE StudentID = %s", (student_id))
            print("get_student_current_balance")
            return cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def make_student_pay(student_id, amount):
    query = """
        UPDATE Student
        SET Balance = Balance - %s
        WHERE StudentID = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (amount, student_id))
    return True
def make_transaction(student_id, instructor_id, course_id):
    query = """
        INSERT INTO Transactions (StudentID, InstructorID, Amount)
        VALUES (%s, %s, %s) RETURNING TransactionID;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Count(StudentID) FROM Student_Course WHERE CourseID = %s AND StudentID = %s", (course_id, student_id))
            if not bool(cursor.fetchone()[0]):
                price = get_course_price(course_id)
                balance = get_student_current_balance(str(student_id))
                if balance >= price:
                    cursor.execute(query, (student_id, instructor_id, price))
                    transaction_id = cursor.fetchone()[0]
                    make_student_pay(student_id, price)
                else:
                    return Response({"error": "student has no enough balance to enroll on this course"}, status=status.HTTP_400_BAD_REQUEST)
                return transaction_id
            else:
                return Response({"error": "student is already enrolled in this course"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return (Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST), False)

def check_if_private_course(student_id, courseID):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT SeenStatus FROM Course WHERE CourseID = %s", (courseID,))
            return cursor.fetchone()[0] == 'private'
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def enroll_student_on_course(student_id, courseID):
    (top_instructor_id, _) = fetch_top_instructor_by_course(courseID)
    returned_value = make_transaction(student_id, top_instructor_id, courseID)
    if isinstance(returned_value, Response):
        return returned_value
    if courseID is None:
        return Response({"error": "Course ID is missing"}, status=status.HTTP_400_BAD_REQUEST)
    query = """
        INSERT INTO Student_Course (CourseID, StudentID, StudentProgress)
        VALUES (%s, %s, %s);
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (courseID, student_id, 0))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    sections = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM CourseSection
                WHERE courseid = %s;
            """, (courseID,))
            section_rows = cursor.fetchall()
            section_columns = [col[0] for col in cursor.description]
            sections.append([dict(zip(section_columns, row)) for row in section_rows])
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    sections = fetch_assignments(sections)
    if isinstance(sections, Response):
        return sections
    assignmentIDs = []
    for outer_section in sections:
        for inner_section in outer_section:
            for assignment in inner_section["assignment"]:
                assignmentIDs.append(assignment['assignmentid'])
    
    for assignmentID in assignmentIDs:
        returned_value = add_assignment_to_student(studentID=student_id, assignmentID=assignmentID)
        if isinstance(returned_value, Response):
            return returned_value
    return Response({"message": "Student Enrollment succesfully"}, status=status.HTTP_200_OK)

def delete_whiteboard_item(item_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM InstructorWhiteBoard WHERE InstructorWhiteBoardID = %s", (item_id,))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def fetch_whiteboard_item(item_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM InstructorWhiteBoard WHERE InstructorWhiteBoardId = %s", (item_id,))
            row = cursor.fetchone()
            column = [col[0] for col in cursor.description]
            return dict(zip(column, row))
    except Exception as e:
        return (Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST), False)

def delete_assignment(assignment_id):
    try:
        query = """
            DELETE FROM Assignment
            WHERE AssignmentID = %s;
        """
        with connection.cursor() as cursor:
            cursor.execute(query, (assignment_id,))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def delete_contest(contest_id):
    try:
        query = """
            DELETE FROM ContestExam
            WHERE ContestExamID = %s;
        """
        with connection.cursor() as cursor:
            cursor.execute(query, (contest_id,))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def delete_quiz(quiz_id):
    try:
        query = """
            DELETE FROM QuizExam
            WHERE QuizExamID = %s;
        """
        with connection.cursor() as cursor:
            cursor.execute(query, (quiz_id,))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True

def get_message_sender_id(message_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT SenderStudentID, SenderInstructorID FROM Message WHERE MessageID = %s", (message_id,))
            row = cursor.fetchall()
            if row[0] is None:
                return row[1]
            return row[0]
    except Exception as e:
        return (Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST), False)

def get_last_watched_video_course(student_id):
    query = """
        SELECT vs.VideoID, vs.VideoProgress
        FROM Video_Student AS vs INNER JOIN Course AS c
        ON vs.CourseID = c.CourseID
        WHERE vs.StudentID = %s
        ORDER BY vs.VideoID DESC
        LIMIT 1;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (student_id,))
            row = cursor.fetchall()
            if len(row) == 0:
                return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row[0]))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get_how_many_watched_video(video, min_value, max_value):
    video_id = video['videoid']
    print(video)
    print("video_id: ", video_id)
    print(min_value)
    print(max_value)
    query = """
        SELECT COUNT(*)
        FROM Video_Student
        WHERE VideoID = %s AND VideoProgress BETWEEN %s AND %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (video_id, min_value, max_value))
            return cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get_review_student_id(review_id):
    query = """
        SELECT StudentID
        FROM FeedBack_Reviews
        WHERE ReviewID = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (review_id,))
            return cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CreateCourseView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        title = request.data.get('title', None)
        description = request.data.get('description', None)
        categoryID = request.data.get("categoryID", None)
        seen_status = request.data.get("seen_status", None)
        price = request.data.get("price", None)
        requirements = request.data.get('requirements', [])
        duration = request.data.get('duration', "0")
        course_image = request.data.get('course_image', None)
        certificate = request.data.get('certificate', None)
        sections = request.data.get('sections', None)
        if title is None or description is None or categoryID is None or seen_status is None or price is None or sections is None or course_image is None or duration is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = self.helper_create_course(request=request, title=title, description=description, categoryID=categoryID, seen_status=seen_status,
            price=price, requirements=requirements, course_image=course_image, duration=duration, certificate=certificate)
        if isinstance(returned_value, Response):
            return returned_value
        else:
            course_id = returned_value
        returned_value = add_sections(sections=sections, course_id=course_id, user_id=request.user['id'])
        if isinstance(returned_value, Response):
            return returned_value
        (sectionIDs, quiz_messages) = returned_value
        return Response({
            "message": "Course created successfully",
            "sectionIDs": sectionIDs,
            "quiz_messages": quiz_messages
        }, status=status.HTTP_201_CREATED)
    
    def helper_create_course(self, request, title, description, categoryID, seen_status, price,
            requirements, course_image, duration, certificate):
        query = """
            INSERT INTO course (title, description, categoryid, seenstatus, price, requirements, topinstructorID, duration)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING courseID;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE Categories SET NumOfCourses = NumOfCourses + 1 WHERE CategoryID = %s", (categoryID,))
                cursor.execute(query, (title, description, categoryID, seen_status, price, requirements, request.user["id"],
                    convert_seconds_to_interval(duration)))
                course_id = cursor.fetchone()[0]
        except Exception as e:
            return Response({"errors": str(e),}, status=status.HTTP_400_BAD_REQUEST)
        if course_image is not None:
            try:
                course_image_file = decode_base64_to_file(course_image)
                upload_result = cloudinary.uploader.upload(course_image_file)
                image_url = upload_result['secure_url']
                query = """
                    UPDATE course
                    SET courseimage = %s
                    WHERE courseid = %s;
                """ 
                with connection.cursor() as cursor:
                    cursor.execute(query, (image_url, course_id))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if certificate is not None:
            try:
                certificate_file = decode_base64_to_file(certificate)
                upload_result = cloudinary.uploader.upload(certificate_file)
                image_url = upload_result['secure_url']
                query = """
                    UPDATE course
                    SET certificate = %s
                    WHERE courseid = %s;
                """
                with connection.cursor() as cursor:
                    cursor.execute(query, (image_url, course_id))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return course_id   
class GetInstructorCourses(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def get(self, request):
        top_instructor_query = "SELECT * FROM course WHERE topinstructorid = %s"
        returned_value = fetch_courses(query=top_instructor_query, param=request.user['id'])
        if isinstance(returned_value, Response):
            return returned_value
        top_instructor_courses = returned_value
        non_top_instructor_query = """
            SELECT c.* 
            FROM course AS c INNER JOIN course_instructor AS ci
            ON c.CourseID = ci.CourseID
            WHERE instructorid = %s
        """
        returned_value = fetch_courses(query=non_top_instructor_query, param=request.user['id'])
        if isinstance(returned_value, Response):
            return returned_value
        non_top_instructor_courses = returned_value
        return Response({
            "top_instructor_courses": top_instructor_courses,
            "non_top_instructor_courses": non_top_instructor_courses
        }, status=status.HTTP_200_OK)
class GetQuizExamView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, quizID):
        query = """
            SELECT q.* FROM Questions AS q INNER JOIN QuizExam AS qe
            ON q.QuizExamID = qe.QuizExamID
            WHERE qe.QuizExamID = %s
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (quizID,))
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                questions = [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Questions": questions}, status=status.HTTP_200_OK)
class GetStudentCourses(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def get(self, request):
        query = "SELECT * FROM student_course AS sc INNER JOIN course AS c ON sc.courseid = c.courseid and sc.studentid = %s;"
        returned_value = fetch_courses(query=query, param=request.user["id"], student_id=request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        courses = returned_value
        return Response(courses, status=status.HTTP_200_OK)
class StudentEnrollmentView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        courseID = request.data.get("courseID", None)
        return enroll_student_on_course(request.user['id'], courseID)
        
class AskInQAVideoView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        video_id = request.data.get("videoID", None)
        question = request.data.get("question", "")
        if video_id is None or question == "":
            return Response({"error": "videoID is missing"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO Messages (MessageText, isAnswer, AnswerTo, SenderStudentID, SenderInstructorID, QAID, ChatID)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO QA (VideoID) VALUES (%s) RETURNING QAID", (video_id,))
                QAID = cursor.fetchone()[0]
                cursor.execute(query, (question, False, None, request.user['id'], None, QAID, None))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Question succesfully asked"}, status=status.HTTP_200_OK)
class GetQAMessages(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, qaid):
        qaid = int(qaid)
        question_query = """
            SELECT * FROM Messages
            WHERE QAID = %s AND isAnswer = %s;
        """
        answers_query = """
            SELECT * FROM Messages
            WHERE QAID = %s AND isAnswer = %s;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(question_query, (qaid, False))
                question_rows = cursor.fetchall()
                question_columns = [col[0] for col in cursor.description]
                questions = [dict(zip(question_columns, row)) for row in question_rows]

                cursor.execute(answers_query, (qaid, True))
                answer_rows = cursor.fetchall()
                answer_columns = [col[0] for col in cursor.description]
                answers = [dict(zip(answer_columns, row)) for row in answer_rows]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"questions": questions[0], "answers": answers}, status=status.HTTP_200_OK)
class GetVideoQA(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, video_id):
        video_id = int(video_id)
        query = """
            SELECT m.*, qa.QAID FROM Messages AS m
            INNER JOIN QA as qa
            ON m.QAID = qa.QAID
            WHERE qa.VideoID = %s AND m.isAnswer = %s;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (video_id, False))
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                messages = [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"qa_questions": messages}, status=status.HTTP_200_OK)
class DeleteQAView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request, qaid):
        qaid = int(qaid)
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM QA WHERE QAID = %s;", (qaid,))
                connection.commit()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Question deleted"}, status=status.HTTP_200_OK)
class EditMessage(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def put(self, request):
        course_id = request.data.get('course_id', None)
        message_id = request.data.get('message_id', None)
        message = request.data.get('message', None)
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        sender_id = get_message_sender_id(message_id)
        if course_id is None or message_id is None or message is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        if top_instructor_id == request.user['id'] or sender_id == request.user['id']:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE Messages SET MessageText = %s WHERE MessageID = %s;", (message, message_id))
                    return Response({"message": "Message updated"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "You are not authorized to edit this message"}, status=status.HTTP_403_FORBIDDEN)
class DeleteMessage(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def put(self, request):
        course_id = request.data.get('course_id', None)
        message_id = request.data.get('message_id', None)
        (top_instructor_id, _) = fetch_top_instructor_by_course(int(course_id))
        sender_id = get_message_sender_id(int(message_id))
        if course_id is None or message_id is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        if top_instructor_id == request.user['id'] or sender_id == request.user['id']:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM Messages WHERE MessageID = %s;", (message_id,))
                    return Response({"message": "Message deleetd"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "You are not authorized to delete this message"}, status=status.HTTP_403_FORBIDDEN)

class InstructorAnswerInQAVideoView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        videoID = request.data.get("videoID", None)
        answerToID = request.data.get("answerToID", None)
        answer = request.data.get("answer", "")
        QAID = request.data.get("QAID", None)
        if videoID is None or answer == "" or answerToID is None or QAID is None:
            return Response({"error": "smth is missing"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO Messages (MessageText, isAnswer, AnswerTo, SenderStudentID, SenderInstructorID, QAID, ChatID)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (answer, True, answerToID, None, request.user['id'], QAID, None))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Instructor Answered"}, status=status.HTTP_200_OK)
class StudentAnswerInQAVideoView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        videoID = request.data.get("videoID", None)
        answerToID = request.data.get("answerToID", None)
        answer = request.data.get("answer", "")
        QAID = request.data.get("QAID", None)
        if videoID is None or answer == "" or answerToID is None or QAID is None:
            return Response({"error": "smth is missing"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO Messages (MessageText, isAnswer, AnswerTo, SenderStudentID, SenderInstructorID, QAID, ChatID)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (answer, True, answerToID, request.user['id'], None, QAID, None))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Student Answered"}, status=status.HTTP_200_OK)
class AddQuizView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        title = request.data.get("title", None)
        sectionID = request.data.get("sectionID", None)
        questions = request.data.get("questions", None)
        quizDuration = request.data.get("quizDuration", None)
        totalMarks = request.data.get("totalMarks", None)
        passingMarks = request.data.get("passingMarks", None)
        if title is None or questions is None or quizDuration is None or totalMarks is None or passingMarks is None:
            return Response({"error": "smth is missing"}, status=status.HTTP_400_BAD_REQUEST)
        (top_instructor_id, course_id) = fetch_top_instructor_by_section(sectionID)
        if isinstance(top_instructor_id, Response):
            return top_instructor_id
        if top_instructor_id is None:
            return Response({"error": "smth wrong in data"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = create_quiz(title=title, sectionID=sectionID, questions=questions, quizDuration=quizDuration, totalMarks=totalMarks,
            passingMarks=passingMarks, user_id=request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        if request.user['id'] != top_instructor_id:
            query = """
                INSERT INTO InstructorWhiteBoard (InstructorID, CourseID, AssignmentID, QuizExamID, ContestExamID)
                VALUES (%s, %s, %s, %s, %s);
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query, (request.user['id'], course_id, None, returned_value, None))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Quiz Added"}, status=status.HTTP_200_OK)

class AddInstructorToCourseView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        courseID = request.data.get("courseID", None)
        instructor_list = request.data.get("instructors", [])
        if courseID is None or instructor_list is None:
            return Response({"error": "smth is missing"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            SELECT TopInstructorID FROM Course WHERE CourseID = %s
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (courseID,))
                topInstructorID = cursor.fetchone()[0]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if request.user["id"] != topInstructorID:
            return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_403_FORBIDDEN)
        if len(instructor_list) == 0:
            return Response({"error": "No instructors selected"}, status=status.HTTP_400_BAD_REQUEST)
        get_id_query = """
            SELECT InstructorID FROM Instructor WHERE Username = %s;
        """
        insert_query = """
            INSERT INTO Course_Instructor (CourseID, InstructorID)
            VALUES (%s, %s);
        """
        instructorsIDs = []
        for instructor in instructor_list:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(get_id_query, (instructor,))
                    instructorID = cursor.fetchone()[0]
                    instructorsIDs.append(instructorID)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        for instructorID in instructorsIDs:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(insert_query, (courseID, instructorID))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Instructors Added"}, status=status.HTTP_200_OK)
class AddAssignment(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        courseID = request.data.get("courseID", None)
        sectionID = request.data.get("sectionID", None)
        title = request.data.get("title", None)
        description = request.data.get("description", None)
        maxMarks = request.data.get("maxMarks", None)
        passingMarks = request.data.get("passingMarks", None)
        assignment_file = request.FILES.get("assignment_file", None)
        if courseID is None or sectionID is None or title is None or description is None or maxMarks is None or passingMarks is None:
            return Response({"error": "smth is missing"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = create_assignment(title=title, description=description, sectionID=sectionID,
            maxMarks=maxMarks, passingMarks=passingMarks, assignment_file=assignment_file)
        if isinstance(returned_value, Response):
            return returned_value
        assignmentID = returned_value
        (top_instructor_id, course_id) = fetch_top_instructor_by_course(courseID)
        if isinstance(top_instructor_id, Response):
            return top_instructor_id
        if top_instructor_id is None:
            return Response({"error": "smth wrong in data"}, status=status.HTTP_400_BAD_REQUEST)
        if request.user['id'] == top_instructor_id:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT StudentID FROM Student_Course WHERE CourseID = %s", (courseID,))
                    studentsIDs = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            for studentID in studentsIDs:
                returned_value = add_assignment_to_student(studentID=studentID, assignmentID=assignmentID)
                if isinstance(returned_value, Response):
                    return returned_value
        else:
            query = """
                INSERT INTO InstructorWhiteBoard (InstructorID, CourseID, AssignmentID, QuizExamID, ContestExamID)
                VALUES (%s, %s, %s, %s, %s);
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query, (request.user['id'], course_id, assignmentID, None, None))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Assignment Added"}, status=status.HTTP_200_OK)
class SubmitAssignmentView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        StudentAssignmentID = request.data.get("studentAssignmentID", None)
        submission_file = request.FILES.get("submission_file", None)
        if StudentAssignmentID is None or submission_file is None:
            return Response({"error": "Assignment ID and Submission File are required"}, status=status.HTTP_400)
        try:
            upload_result = cloudinary.uploader.upload(submission_file, resource_type="raw")
            file_url = upload_result['secure_url']
            query = """
                UPDATE Student_Assignment
                SET SubmissionLink = %s, Status = %s
                WHERE StudentAssignmentID = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (file_url, 'submitted', StudentAssignmentID))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Assignment submitted successfully"}, status=status.HTTP_200_OK)    
class GradeAssignment(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        studentAssignmentID = request.data.get("studentAssignmentID", None)
        grade = request.data.get("grade", None)
        if studentAssignmentID is None or grade is None:
            return Response({"error": "Assignment ID, Student Assignment ID and Grade are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            query = """
                SELECT a.MaxMarks FROM Student_Assignment AS sa
                INNER JOIN Assignment AS a
                ON sa.AssignmentID = a.AssignmentID
                WHERE sa.StudentAssignmentID = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (studentAssignmentID,))
                max_marks = cursor.fetchone()[0]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            query = """
                UPDATE Student_Assignment
                SET Grade = %s, Status = %s, submissiondate = %s, PassFail = %s
                WHERE StudentAssignmentID = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (grade, "graded", datetime.now(), grade >= max_marks // 2, studentAssignmentID))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Assignment graded successfully"}, status=status.HTTP_200_OK)
class DeleteCourseView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request, courseId):
        try:
            query = """
                DELETE FROM Course
                WHERE CourseID = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute("SELECT CategoryID FROM Course WHERE CourseID = %s", (courseId,))
                categoryID = cursor.fetchone()[0]
                cursor.execute(query, (courseId,))
                cursor.execute("UPDATE Categories SET NumOfCourses = NumOfCourses - 1 WHERE CategoryID = %s", (categoryID,))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Course deleted successfully"}, status=status.HTTP_200_OK)
class DeleteSectionView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request, sectionId):
        try:
            query = """
                DELETE FROM CourseSection
                WHERE CourseSectionID = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (sectionId,))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Section deleted successfully"}, status=status.HTTP_200_OK)
class DeleteVideoView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request, videoId):
        try:
            query = """
                DELETE FROM Video
                WHERE VideoID = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (videoId,))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Video deleted successfully"}, status=status.HTTP_200_OK)
class DeleteAssignmentView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request, assignmentId):
        returned_value = delete_assignment(assignmentId)
        if isinstance(returned_value, Response):
            return returned_value
        Response({"message": "Assignment deleted successfully"}, status=status.HTTP_200_OK)
class DeleteQuizView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request, quizId):
        returned_value = delete_quiz(quizId)
        if isinstance(returned_value, Response):
                return returned_value
        return Response({"message": "Quiz deleted successfully"}, status=status.HTTP_200_OK)
class UpdateQuizView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def put(self, request, quizId):
        quizzes = request.data.get("quizzes", [])
        for quiz in quizzes:
            returned_value = update_quiz(data=quiz, quizID=quiz.get("quizId", None))
            if isinstance(returned_value, Response):
                return returned_value
        return Response({"message": "Quiz succesfully updated"}, status=status.HTTP_200_OK)
class UpdateAssignment(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def put(self, request, assignmentId):
        data = request.data
        FILES = request.FILES
        returned_value = update_assignment(data=data, FILES=FILES, assignmentID=assignmentId)
        if isinstance(returned_value, Response):
            return returned_value
        return Response({"message": "Assignment succesfully updated"}, status=status.HTTP_200_OK)
class UpdateVideo(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def put(self, request):
        videos = request.data.get("videos", [])
        for video in videos:
            returned_value = update_video(data=video)
            if isinstance(returned_value, Response):
                return returned_value
        return Response({"message": "Video succesfully updated"}, status=status.HTTP_200_OK)
class UpdateSectionView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def put(self, request):
        sections = request.data.get("sections", [])
        for section in sections:
            sectionId = section.get("sectionId", None)
            returned_value = update_section(data=section, sectionID=sectionId)
            if isinstance(returned_value, Response):
                return returned_value
        return Response({"message": "Sections succesfully updated"}, status=status.HTTP_200_OK)
class AddVideo(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        videos = request.data.get("videos", [])
        for video in videos:
            section_id = video.get("section_id", None)
            video_title = video.get("title", None)
            video = video.get('video', None)
            if section_id is None or video_title is None or video is None:
                return Response({"message": "Please provide all required fields"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                video_file = decode_base64_to_file(video)
                upload_result = cloudinary.uploader.upload(video_file, resource_type='video', format='mp4')
                video_url = upload_result['secure_url']
                create_video_query = """
                    INSERT INTO video (coursesectionid, title, videolink)
                    VALUES (%s, %s, %s)
                """
                with connection.cursor() as cursor:
                    cursor.execute(create_video_query, (section_id, video_title, video_url))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Videos succesfully added"}, status=status.HTTP_200_OK)
class MakeContest(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        title = request.data.get("title", None)
        coureseId = request.data.get("courseId", None)
        questions = request.data.get("questions", None)
        quizDuration = request.data.get("quizDuration", None)
        totalMarks = request.data.get("totalMarks", None)
        passingMarks = request.data.get("passingMarks", None)
        if title is None or coureseId is None or questions is None or quizDuration is None:
            return Response({"message": "Please provide all required fields"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = create_contest(title=title, courseId=coureseId, questions=questions, quizDuration=quizDuration, totalMarks=totalMarks,
            passingMarks=passingMarks, user_id=request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        contest_id = returned_value
        (top_instructor_id, course_id) = fetch_top_instructor_by_course(coureseId)
        if isinstance(top_instructor_id, Response):
            return top_instructor_id
        if top_instructor_id is None:
            return Response({"error": "smth wrong in data"}, status=status.HTTP_400_BAD_REQUEST)
        if request.user['id'] != top_instructor_id:
            query = """
                INSERT INTO InstructorWhiteBoard (InstructorID, CourseID, AssignmentID, QuizExamID, ContestExamID)
                VALUES (%s, %s, %s, %s, %s);
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query, (request.user['id'], course_id, None, None, contest_id))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Contest succesfully created"}, status=status.HTTP_200_OK)
class GetCourseWhiteBoard(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def get(self, request, courseId):
        if courseId is None:
            return Response({"message": "Please provide course id"}, status=status.HTTP_400_BAD_REQUEST)
        (top_instructor_id, courseId) = fetch_top_instructor_by_course(courseId)
        print("user: ", request.user['id'])
        print("top: ", top_instructor_id)
        if request.user['id'] == top_instructor_id:
            items = fetch_whiteboard(courseId)
            if isinstance(items, Response):
                return items
            return Response({
                "whiteboard": items
            }, status=status.HTTP_200_OK)
        return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_400_BAD_REQUEST)
class DeleteContest(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request, contestId):
        returned_value = delete_contest(contestId)
        if isinstance(returned_value, Response):
                return returned_value
        return Response({"message": "Contest deleted successfully"}, status=status.HTTP_200_OK)
class AddSectionsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        course_id = request.data.get("courseId", None)
        sections = request.data.get("sections", [])
        if course_id is None:
            return Response({"message": "Please provide all required fields"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = add_sections(sections, course_id, request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        return Response({"message": "Sections succesfully added"}, status=status.HTTP_200_OK)
class GetCategories(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Categories")
                categories = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                categories = [dict(zip(columns, category)) for category in categories]
                return Response({"categories": categories}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 
class SearchByTtitle(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        title = request.data.get("title", None)
        if title is None:
            return Response({"message": "Please provide all required fields"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            SELECT * FROM Course
            WHERE Title ILIKE %s;
        """
        title = f"%{title}%"
        courses = fetch_courses(query, title)
        if isinstance(courses, Response):
            return courses
        return Response({"courses": courses}, status=status.HTTP_200_OK)
class SearchByCategories(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        categories = request.data.get("categories", [])
        query = """
            SELECT * FROM Course WHERE CategoryID = %s
        """
        courses = []
        for category in categories:
            returned_value = fetch_courses(query, category)
            if isinstance(returned_value, Response):
                return returned_value
            courses.append(returned_value)
        return Response({"courses": courses}, status=status.HTTP_200_OK)      
class SearchByTitleAndCategories(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        title = request.data.get("title", None)
        categories = request.data.get("categories", [])
        query = """
            SELECT * FROM Course WHERE CategoryID = %s AND Title ILIKE %s;
        """
        courses = []
        for category in categories:
            returned_value = fetch_courses(query, (category, f"%{title}%"))
            if isinstance(returned_value, Response):
                return returned_value
            courses.append(returned_value)
        return Response({"courses": courses}, status=status.HTTP_200_OK)      
class GetSingleCourse(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def get(self, request, course_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM course WHERE courseid = %s", (course_id,))
                columns = [col[0] for col in cursor.description]  # Get column names
                rows = cursor.fetchall()
                course_data = [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "course": course_data
        }, status=status.HTTP_200_OK)
class IncreaseStudentBalanceView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request, amount):
        query = """
            UPDATE Student
            SET Balance = %s
            WHERE StudentID = %s
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (amount, request.user['id']))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Balance increased successfully"}, status=status.HTTP_200_OK)
class GetUserTransactions(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                if request.auth == 'student':
                    cursor.execute("SELECT * FROM Transactions WHERE StudentID = %s", (request.user['id'],))
                elif request.auth == 'instructor':
                    cursor.execute("SELECT * FROM Transactions WHERE InstructorID = %s", (request.user['id'],))
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                transactions_data = [dict(zip(columns, row)) for row in rows]
                return Response({"transactions": transactions_data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AcceptWhiteBoardItemView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request):
        course_id = request.data.get("course_id", None)
        item_id = request.data.get("item_id", None)
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        if top_instructor_id != request.user['id']:
            return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = delete_whiteboard_item(item_id)
        if isinstance(returned_value, Response):
            return returned_value
        return Response({"message": "Whiteboard item deleted successfully"}, status=status.HTTP_200_OK)
class RejectWhiteBoardItemView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request):
        course_id = request.data.get("course_id", None)
        item_id = request.data.get("item_id", None)
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        if top_instructor_id != request.user['id']:
            return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_400_BAD_REQUEST)
        item = fetch_whiteboard_item(item_id)
        print(item)
        if isinstance(item, Response):
            return item
        if item['assignmentid'] is not None:
            returned_value = delete_assignment(int(item['assignmentid']))
        elif item['quizexamid'] is not None:
            returned_value = delete_quiz(int(item['quizexamid']))
        elif item['contestexamid'] is not None:
            returned_value = delete_contest(int(item['contestexamid']))
        if isinstance(returned_value, Response):
            return returned_value
        return Response({"message": "Whiteboard item deleted successfully"}, status=status.HTTP_200_OK)
class StudentEnrollmentInPrivateCourse(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request, course_id):
        returned_value = check_if_private_course(course_id)
        if isinstance(returned_value, Response):
            return returned_value
        if returned_value:
            enroll_student_on_course(request.user['id'], course_id)
        else:
            return Response({"error": "Course is not private"}, status=status.HTTP_400_BAD_REQUEST)

class MakeAnnouncementView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        announcement = request.data('announcement', None)
        course_id = request.data.get('course_id', None)
        if announcement is None or course_id is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        if top_instructor_id != request.user['id']:
            return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = check_if_private_course(course_id)
        if isinstance(returned_value, Response):
            return returned_value
        if returned_value:
            query = """
                INSERT INTO CourseAnnouncements (AnnouncerID, CourseID, Announcement)
                VALUES (%s, %s, %s)
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query, (request.user['id'], course_id, announcement))
                    return Response({"message": "Announcement made successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Course is not private"}, status=status.HTTP_400_BAD_REQUEST)
class UpdateAnnouncementView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        announcement = request.data('announcement', None)
        course_id = request.data.get('course_id', None)
        announcement_id = request.data.get('announcement_id', None)
        if announcement is None or course_id is None or announcement_id is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        if top_instructor_id != request.user['id']:
            return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = check_if_private_course(course_id)
        if isinstance(returned_value, Response):
            return returned_value
        if returned_value:
            query = """
                UPDATE CourseAnnouncements
                SET Announcement = %s
                WHERE AnnouncementID = %s
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query, (announcement, announcement_id))
                    return Response({"message": "Announcement updated successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Course is not private"}, status=status.HTTP_400_BAD_REQUEST)  
class GetAnnouncementsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def get(self, request, course_id):
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        if top_instructor_id != request.user['id']:
            return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = check_if_private_course(course_id)
        if isinstance(returned_value, Response):
            return returned_value
        if returned_value:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM CourseAnnouncements WHERE CourseID = %s;", (course_id))
                    announcements_rows = cursor.fetchall()
                    announcements_cols = [col[0] for col in cursor.description]
                    announcements = [dict(zip(announcements_cols, row)) for row in announcements_rows]
                    return Response(announcements, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Course is not private"}, status=status.HTTP_400_BAD_REQUEST)

class UpdateStudentVideoProgress(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        course_id = request.data.get('course_id', None)
        student_id = request.data.get('student_id', None)
        video_id = request.data.get('video_id', None)
        progress = request.data.get('progress', None)
        if student_id is None or video_id is None or progress is None or course_id is None:
            return Response({"error": "Student ID, Video ID, Course ID and Progress are required"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO Video_Student (VideoID, StudentID, VideoProgress, CourseID)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (VideoID, StudentID)
            DO UPDATE SET VideoProgress = EXCLUDED.VideoProgress;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (video_id, student_id, progress, course_id))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Video progress updated successfully"}, status=status.HTTP_200_OK)
class GetCourseStatistics(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def get(self, request, course_id):
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        if top_instructor_id != request.user['id']:
            return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_403_FORBIDDEN)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM Student_Course WHERE CourseID = %s;", (course_id,))
                total_students = cursor.fetchone()[0]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        sections = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT CourseSectionID, Title FROM CourseSection
                    WHERE courseid = %s;
                """, (course_id,))
                section_rows = cursor.fetchall()
                section_columns = [col[0] for col in cursor.description]
                sections = [dict(zip(section_columns, row)) for row in section_rows]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        for i, section in enumerate(sections):
            section_id = section['coursesectionid']
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM Video
                        WHERE CourseSectionID = %s;
                    """, (section_id,))
                    videos_rows = cursor.fetchall()
                    videos_cols = [col[0] for col in cursor.description]
                    videos = [dict(zip(videos_cols, row)) for row in videos_rows]
                    sections[i]["videos"] = videos
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        for i, section in enumerate(sections):
            section_videos = sections[i]["videos"]
            for j, video in enumerate(section_videos):
                returned_value = get_how_many_watched_video(video, 0, 25)
                if isinstance(returned_value, Response):
                    return returned_value
                sections[i]["videos"][j]['quarter'] = returned_value
                
                returned_value = get_how_many_watched_video(video, 25, 50)
                if isinstance(returned_value, Response):
                    return returned_value
                sections[i]["videos"][j]['half'] = returned_value

                returned_value = get_how_many_watched_video(video, 50, 75)
                if isinstance(returned_value, Response):
                    return returned_value
                sections[i]["videos"][j]['threequarters'] = returned_value

                returned_value = get_how_many_watched_video(video, 50, 75)
                if isinstance(returned_value, Response):
                    return returned_value
                sections[i]["videos"][j]['full'] = returned_value
        return Response({
            "total_students": total_students,
            "sections": sections
        }, status=status.HTTP_200_OK)

class AddFeedbackReviewToCourseView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        rating = request.data.get('rating', None)
        course_id = request.data.get('course_id', None)
        review = request.data.get('review', None)
        if course_id is None or review is None or rating is None:
            return Response({"error": "Course ID and review are required"}, status=status.HTTP_400_BAD)
        query = """
            INSERT INTO FeedBack_Reviews (CourseID, InstructorID, Review, Rating)
            VALUES (%s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (course_id, None, review, rating))
                return Response({"message": "Feedback review added successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class AddFeedbackReviewToInstructorView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        rating = request.data.get('rating', None)
        instructor_id = request.data.get('course_id', None)
        review = request.data.get('review', None)
        if instructor_id is None or review is None or rating is None:
            return Response({"error": "Instructor ID and review are required"}, status=status.HTTP_400_BAD)
        query = """
            INSERT INTO FeedBack_Reviews (CourseID, InstructorID, Review, Rating)
            VALUES (%s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (None, instructor_id, review, rating))
                return Response({"message": "Feedback review added successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class EditFeedBackView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def put(self, request):
        ReviewID = request.data.get('review_id', None)
        rating = request.data.get('rating', None)
        review = request.data.get('review', None)
        if ReviewID is None or review is None or rating is None:
            return Response({"error": "Review ID, review and rating are required"}, status=status.HTTP_400_BAD_REQUEST)
        student_id = get_review_student_id(ReviewID)
        if student_id != request.user['id']:
            return Response({"error": "You are not the owner of this review"}, status=status.HTTP_403_FORBIDDEN)
        query = """
            UPDATE FeedBack_Reviews
            SET Rating = %s, Review = %s
            WHERE ReviewID = %s;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (rating, review, ReviewID))
                return Response({"message": "FeedBack review updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class DeleteFeedbackView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def delete(self, request, review_id):
        student_id = get_review_student_id(review_id)
        if student_id != request.user['id']:
            return Response({"error": "You are not the owner of this review"}, status=status.HTTP_403_FORBIDDEN)
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM FeedBack_Reviews WHERE ReviewID = %s;", (review_id,))
                return Response({"message": "FeedBack review deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GetFeedBackViewForCourseView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, course_id):
        query = """
            SELECT * FROM FeedBack_Reviews AS fr
            INNER JOIN Student AS s ON fr.StudentID = s.StudentID
            WHERE CourseID = %s;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (course_id,))
                reviews = cursor.fetchall()
                return Response({"reviews": reviews}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class GetFeedBackViewForInstructorView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, instructor_id):
        query = """
            SELECT * FROM FeedBack_Reviews AS fr
            INNER JOIN Student AS s ON fr.StudentID = s.StudentID
            WHERE InstructorID = %s;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (instructor_id,))
                reviews = cursor.fetchall()
                return Response({"reviews": reviews}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DeleteAnnouncementView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request):
        announcement_id = request.data.get('announcement_id')
        course_id = request.data.get('course_id')
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        if top_instructor_id != request.user['id']:
            return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = check_if_private_course(course_id)
        if isinstance(returned_value, Response):
            return returned_value
        if returned_value:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM CourseAnnouncements WHERE AnnouncementID = %s;", (announcement_id,))
                    return Response({"message": "Announcement deleted successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Course is not private"}, status=status.HTTP_400_BAD_REQUEST)