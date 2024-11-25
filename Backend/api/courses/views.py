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

def create_quiz(title, sectionID, questions, quizDuration, totlaMarks, passingMarks, user_id):
    # check is all data is not None
    if title is None or sectionID is None or questions is None or quizDuration is None or totlaMarks is None or passingMarks is None or user_id is None:
        return None
    query = """INSERT INTO QuizExam (Title, SectionID, InstructorID, ExamKind, Duration, TotalMarks, PassingMarks)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING QuizExamID;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (title, sectionID, user_id, 'quiz', convert_seconds_to_interval(quizDuration), totlaMarks, passingMarks))
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
                    sections[i][j]["assignment"].append([dict(zip(section_columns, row)) for row in section_rows])
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

def fetch_courses(query, id):
    courses = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id,))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            courses = [dict(zip(columns, row)) for row in rows]
            course_ids = [course['courseid'] for course in courses]
            sections = []
            for course_id in course_ids:
                cursor.execute("""
                    SELECT * FROM CourseSection
                    WHERE courseid = %s;
                """, (course_id,))
                section_rows = cursor.fetchall()
                section_columns = [col[0] for col in cursor.description]
                sections.append([dict(zip(section_columns, row)) for row in section_rows])
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
                temp_data['sections'] = sections[i]
                data.append(temp_data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return data

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
        returned_value = self.helper_create_sections(sections=sections, course_id=course_id, user_id=request.user['id'])
        if isinstance(returned_value, Response):
            return returned_value
        quiz_messages = returned_value
        return Response({
            "message": "Course created successfully",
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

    def helper_create_sections(self, sections, course_id, user_id):
        quiz_messages = []
        for section in sections:
            section_title = section["title"]
            section_videos = section["videos"]
            create_section_query = """
                INSERT INTO coursesection (courseid, title)
                VALUES (%s, %s) RETURNING CourseSectionID;
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(create_section_query, (course_id, section_title))
                    section_id = cursor.fetchone()[0]
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            if section.get('quiz', None):
                quiz = section['quiz']
                returned_value = create_quiz(title=quiz.get('title', None), sectionID=quiz.get('sectionID', None), questions=quiz.get('questions', None),
                    quizDuration=quiz.get('quizDuration', None), totlaMarks=quiz.get('totlaMarks', None), passingMarks=quiz.get('passingMarks', None),
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
        return quiz_messages 

class GetInstructorCourses(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def get(self, request):
        top_instructor_query = "SELECT * FROM course WHERE topinstructorid = %s"
        returned_value = fetch_courses(query=top_instructor_query, id=request.user['id'])
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
        returned_value = fetch_courses(query=query, id=request.user["id"])
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

class AskInQAVideoView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
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

class AddQuiz(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        title = request.data.get("title", None)
        sectionID = request.data.get("sectionID", None)
        questions = request.data.get("questions", None)
        quizDuration = request.data.get("quizDuration", None)
        totlaMarks = request.data.get("totlaMarks", None)
        passingMarks = request.data.get("totlaMarks", None)
        if title is None or questions is None or quizDuration is None:
            return Response({"error": "smth is missing"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = create_quiz(title=title, sectionID=sectionID, questions=questions, quizDuration=quizDuration, totlaMarks=totlaMarks,
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
        assignment_file = request.FILES.get("assignment_file", None)
        if courseID is None or sectionID is None or title is None or description is None or maxMarks is None:
            return Response({"error": "smth is missing"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO Assignment (Title, Description, CourseSectionID, MaxMarks)
            VALUES (%s, %s, %s, %s) RETURNING AssignmentID;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (title, description, sectionID, maxMarks))
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
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT StudentID FROM Student_Course WHERE CourseID = %s", (courseID,))
                studentsIDs = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        insert_query = """
            INSERT INTO Student_Assignment (StudentID, AssignmentID, SubmissionLink, Grade, SubmissionDate, PassFail)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        for studentID in studentsIDs:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(insert_query, (studentID, assignmentID, None, 0, None, None))
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
                UPDATE Student_Assignment
                SET Grade = %s
                WHERE StudentAssignmentID = %s;
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (grade, studentAssignmentID))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Assignment graded successfully"}, status=status.HTTP_200_OK)

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