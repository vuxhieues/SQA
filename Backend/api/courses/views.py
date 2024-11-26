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
    return True
def fetch_contests(course_id):
    query = """
        SELECT * FROM ContestExam WHERE CourseID = %s;
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
                        WHERE CourseSectionID = %s;
                    """, (inner_section['coursesectionid'],))
                    section_rows = cursor.fetchall()
                    section_columns = [col[0] for col in cursor.description]
                    sections[i][j]['assignment'] = []
                    sections[i][j]["assignment"] = [dict(zip(section_columns, row)) for row in section_rows]
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
def fetch_videos(sections):
    for i, outer_section in enumerate(sections):
        for j, inner_section in enumerate(outer_section):
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM Video
                        WHERE CourseSectionID = %s;
                    """, (inner_section['coursesectionid'],))
                    section_rows = cursor.fetchall()
                    section_columns = [col[0] for col in cursor.description]
                    sections[i][j]['videos'] = []
                    sections[i][j]["videos"].append([dict(zip(section_columns, row)) for row in section_rows])
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
                        WHERE SectionID = %s;
                    """, (inner_section['coursesectionid'],))
                    section_rows = cursor.fetchall()
                    section_columns = [col[0] for col in cursor.description]
                    sections[i][j]['quizzes'] = []
                    sections[i][j]['quizzes'].append([dict(zip(section_columns, row)) for row in section_rows])
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
def fetch_courses(query, param):
    courses = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (param,))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            courses = [dict(zip(columns, row)) for row in rows]
            course_ids = [course['courseid'] for course in courses]
            sections = []
            contests = []
            for course_id in course_ids:
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
            sections = fetch_videos(sections)
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
                        VALUES (%s, %s, %s)
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
        duration = request.data.get('duration', 0)
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
        returned_value = fetch_courses(query=non_top_instructor_query, id=request.user['id'])
        if isinstance(returned_value, Response):
            return returned_value
        non_top_instructor_courses = returned_value
        # try:
        #     with connection.cursor() as cursor:
        #         cursor.execute("SELECT courseid FROM course_instructor WHERE instructorid = %s", (request.user['id'],))
        #         non_top_instructor_coursesIDs = cursor.fetchall()
        # except Exception as e:
        #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # non_top_instructor_courses = []
        # for courseID in non_top_instructor_coursesIDs:
        #     try:
        #         with connection.cursor() as cursor:
        #             cursor.execute("SELECT * FROM course WHERE courseid = %s", (courseID,))
        #             rows = cursor.fetchall()
        #             columns = [col[0] for col in cursor.description]
        #             non_top_instructor_courses = [dict(zip(columns, row)) for row in rows]
        #     except Exception as e:
        #         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
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
        returned_value = fetch_courses(query=query, param=request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        courses = returned_value
        return Response(courses, status=status.HTTP_200_OK)
class StudentEnrollmentView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        courseID = request.data.get("courseID", None)
        if courseID is None:
            return Response({"error": "Course ID is missing"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO Student_Course (CourseID, StudentID, StudentProgress)
            VALUES (%s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (courseID, request.user['id'], 0))
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
            returned_value = add_assignment_to_student(studentID=request.user['id'], assignmentID=assignmentID)
            if isinstance(returned_value, Response):
                return returned_value

        return Response({"message": "Student Enrollment succesfully"}, status=status.HTTP_200_OK)
class AskInQAVideoView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def get(self, request):
        videoID = request.data.get("videoID", None)
        question = request.data.get("question", "")
        if videoID is None or question == "":
            return Response({"error": "videoID is missing"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO Messages (MessageText, isAnswer, AnswerTo, SenderStudentID, SenderInstructorID, QAID, ChatID)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO QA (VideoID) VALUES (%s) RETURNING QAID", (videoID,))
                QAID = cursor.fetchone()[0]
                cursor.execute(query, (question, False, None, request.user['id'], None, QAID, None))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Question succesfully asked"}, status=status.HTTP_200_OK)
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
        returned_value = create_quiz(title=title, sectionID=sectionID, questions=questions, quizDuration=quizDuration, totalMarks=totalMarks,
            passingMarks=passingMarks, user_id=request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
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
        try:
            query = """
                DELETE FROM Assignment
                WHERE AssignmentID = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (assignmentId,))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Assignment deleted successfully"}, status=status.HTTP_200_OK)
class DeleteQuizView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request, quizId):
        try:
            query = """
                DELETE FROM QuizExam
                WHERE QuizExamID = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (quizId,))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
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
        return Response({"message": "Contest succesfully created"}, status=status.HTTP_200_OK)
class DeleteContest(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request, contestId):
        try:
            query = """
                DELETE FROM ContestExam
                WHERE ContestExamID = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (contestId,))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
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