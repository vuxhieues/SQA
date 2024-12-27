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
from urllib.parse import urlparse
from django.template import loader
from django.core.mail import send_mail
from django.utils.html import strip_tags
import copy

# Create your views here.
def extract_public_id(cloudinary_url):
    parsed_url = urlparse(cloudinary_url)
    path = parsed_url.path.split("/upload/")[-1]
    public_id = path.rsplit(".", 1)[0]
    return public_id

def send_email_qa(emails, course_id):
    subject = "New LiveQA Session"
    template = loader.get_template('newQA_template.html')
    html_message = template.render({'session_link': f"https://yomac-public-7m6c.vercel.app/liveqa/{course_id}"})
    message = strip_tags(html_message)
    send_mail(
        subject=subject,
        message=message,
        from_email="mbahgat503@gmail.com",
        recipient_list=emails,
        html_message=html_message
    )

def decode_base64_to_file(base64_str):
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    file_data = base64.b64decode(base64_str)
    file = io.BytesIO(file_data)
    return file
def convert_seconds_to_interval(seconds):
    print("seconds: ", seconds)
    if seconds is None:
        return None
    if isinstance(seconds, str):
        return seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds -= hours*60*60 + minutes*60
    return f"{hours} hours {minutes} minutes {seconds} seconds"
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
        WHERE QuestionID = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(update_quiz_query, (title, convert_seconds_to_interval(quizDuration), totalMarks, passingMarks, quizID))
            for question in questions:
                cursor.execute(update_quiz_questions_query, (question['questiontext'], question['choices'],
                    question['correctanswerindex'], question["questionid"]))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def update_assignment(data, FILES = None):
    assignmentID = data.get("assignmentID", None)
    title = data.get("title", None)
    description = data.get("description", None)
    maxMarks = data.get("maxMarks", None)
    passingMarks = data.get("passingMarks", None)
    message = "No file"
    if assignmentID is None or title is None or description is None or maxMarks is None or passingMarks is None:
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
    if FILES is not None:
        assignment_file = FILES.get("assignment_file", None)
        if assignment_file is None:
            return Response({"error": "Assignment file is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT FileAttched FROM Assignment WHERE AssignmentID = %s", (assignmentID,))
            file_attached = cursor.fetchone()[0]
            new_file_url = file_attached
            if FILES is not None:
                file_attached = extract_public_id(file_attached)
                try:
                    upload_result = cloudinary.uploader.upload(assignment_file, resource_type="raw", public_id=file_attached, overwrite=True)
                    new_file_url = upload_result['secure_url']
                    message = "File"
                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)          
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    update_assignment_query = """
        UPDATE Assignment
        SET Title = %s, Description = %s, MaxMarks = %s, PassingMarks = %s, FileAttched = %s
        WHERE AssignmentID = %s;
    """
    print("message::::::::: ", message)
    try:
        with connection.cursor() as cursor:
            cursor.execute(update_assignment_query, (title, description, maxMarks, passingMarks, new_file_url, assignmentID))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def update_video(data):
    course_id = data.get("course_id", None)
    old_duration = data.get("old_duration", None)
    videoID = data.get("videoID", None)
    video_title = data.get("title", None)
    video_duration = data.get("duration", 0)
    video = data.get('video', None)
    if videoID is None or video_title is None:
        return Response({"error": "Video title and video are required"}, status=status.HTTP_400_BAD_REQUEST)
    # try:
    #     with connection.cursor() as cursor:
    #         cursor.execute("SELECT VideoLink, EXTRACT(epoch FROM VideoDuration) FROM Video WHERE VideoID = %s", (videoID,))
    #         video_attached, old_video_duration = cursor.fetchone()
    #         print("video_attached: ", video_attached)
    #         new_video_url = video_attached
    #         if video is not None:
    #             video_attached = extract_public_id(video_attached)
    #             try:
    #                 video_file = decode_base64_to_file(video)
    #                 print(video_file)
    #                 upload_result = cloudinary.uploader.upload(video_file, public_id=video_attached, resource_type="video", format='mp4')
    #                 new_video_url = upload_result['secure_url']
    #             except Exception as e:
    #                 return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    #         else:
    #             video_duration = old_duration      
    # except Exception as e:
    #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    # print(new_video_url)
    update_video_query = """
        UPDATE Video
        SET title = %s
        WHERE VideoID = %s
    """
    try:
        # print("video_duration: ", video_duration)
        # print("video_duration: ", videoID)
        with connection.cursor() as cursor:
            cursor.execute(update_video_query, (video_title, videoID))
            # cursor.execute("DELETE FROM Video_Student WHERE VideoID = %s", (videoID,))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    # if old_duration is None or course_id is None: 
    #     old_course_duration = get_course_duration_by_courseid(course_id)
    #     if isinstance(old_course_duration, Response):
    #         return old_course_duration
    #     old_course_duration = int(old_course_duration)
    #     new_course_duration = convert_seconds_to_interval(old_course_duration - old_duration + video_duration)
    #     print(new_course_duration)
    #     returned_value = update_course_duration(course_id, new_course_duration)
    #     if isinstance(returned_value, Response):
    #         return returned_value
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
    assignments = data.get("assignments", [])
    if len(assignments) > 0:
        for assignment in assignments:
            print("assignments: ", assignment)
            returned_value = update_assignment(assignment)
            if isinstance(returned_value, Response):
                return returned_value
    print("question")
    # Update Videos #
    # videos = data.get("videos", None)
    # if videos is not None:
    #     for video in videos:
    #         returned_value = update_video(video)
    #         if returned_value is not True:
    #             return returned_value
    return True
def create_contest(title, courseId, questions, quizDuration, totalMarks, passingMarks, user_id, discount, flag):
    # check is all data is not None
    query = """
        INSERT INTO ContestExam (Title, CourseID, InstructorID, ExamKind, Duration, TotalMarks, PassingMarks, Discount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING ContestExamID;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (title, courseId, user_id, 'contest', convert_seconds_to_interval(quizDuration), totalMarks, passingMarks, discount))
            contestID = cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    query = """
        INSERT INTO Questions (QuizExamID, ContestExamID, QuestionText, Choices, CorrectAnswerIndex)
        VALUES (%s, %s, %s, %s, %s);
    """
    for question in questions:
        try:
            if question['correctanswerindex'] < len(question['choices']):
                with connection.cursor() as cursor:
                    cursor.execute(query, (None, contestID, question['questiontext'], question['choices'], question['correctanswerindex']))
            else:
                return Response({"error": "Invalid correct answer index"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    if flag:
        studentIds = get_course_students_ids(courseId)
        for studentId in studentIds:
            add_contest_to_student(studentID=studentId, contestId=contestID)
    return contestID
def create_quiz(title, sectionID, questions, quizDuration, totalMarks, passingMarks, user_id, course_id, flag):
    # check is all data is not None
    print("I am in quiz")
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
    print("questionsssss: ", questions)
    for question in questions:
        print("question: ", question)
        try:
            print(len(question['choices']))
            if question['correctanswerindex'] <= len(question['choices']):
                print("question")
                with connection.cursor() as cursor:
                    print("questio")
                    cursor.execute(query, (quizID, None, question['questiontext'], question['choices'], question['correctanswerindex']))
            else:
                return Response({"error": "Invalid correct answer index"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    if flag:
        studentIds = get_course_students_ids(course_id=course_id)
        for studentId in studentIds:
            add_quiz_to_student(studentID=studentId, quizId=quizID)
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

def get_course_students_ids(course_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT StudentId FROM Student_Course WHERE CourseId = %s", (course_id,))
            students_ids = [row[0] for row in cursor.fetchall()]
            return students_ids
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

################### Add HomeWorks To Students ###################
def add_assignment_to_student(studentID, assignmentID):
    insert_query = """
        INSERT INTO Student_Assignment (StudentID, AssignmentID, SubmissionLink, Grade, SubmissionDate, PassFail)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    print("HI")
    try:
        with connection.cursor() as cursor:
            cursor.execute(insert_query, (studentID, assignmentID, None, None, None, None))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def add_quiz_to_student(studentID, quizId):
    insert_query = """
        INSERT INTO Student_Quiz (QuizExamID, StudentID, Pass, Grade)
        VALUES (%s, %s, %s, %s);
    """
    print("HI")
    try:
        with connection.cursor() as cursor:
            cursor.execute(insert_query, (quizId, studentID, None, None))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
def add_contest_to_student(studentID, contestId):
    insert_query = """
        INSERT INTO Student_Contest (ContestExamID, StudentID, Pass, Grade)
        VALUES (%s, %s, %s, %s);
    """
    print("HI")
    try:
        with connection.cursor() as cursor:
            cursor.execute(insert_query, (contestId, studentID, None, None))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return True
################### Add HomeWorks To Students ###################

#################### Fetch HomeWorks To Students ####################
def fetch_student_assignemnts_in_course(sections, student_id):
    sections = fetch_assignments(sections)
    try:
        with connection.cursor() as cursor:
            for section in sections:
                for i, assignment in enumerate(section['assignment']):
                    assignmentid = assignment['assignmentid']
                    cursor.execute("SELECT * FROM Student_Assignment WHERE AssignmentID = %s AND StudentID = %s", (assignmentid, student_id))
                    student_rows = cursor.fetchall()
                    student_columns = [col[0] for col in cursor.description]
                    student_assignment_data = [dict(zip(student_columns, row)) for row in student_rows]
                    if len(student_assignment_data) == 0:
                        section['assignment'][i]["student"] = {}
                    else:
                        section['assignment'][i]["student"] = student_assignment_data[0]
    except Exception as e:
        print("student_rows")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
def fetch_student_quizzes_in_course(sections, student_id):
    sections = fetch_quizzes_overview(sections)
    if isinstance(sections, Response):
        return sections
    try:
        with connection.cursor() as cursor:
            for section in sections:
                for i, quiz in enumerate(section['quizzes']):
                    quizid = quiz['quizexamid']
                    print("student id::: ", student_id)
                    cursor.execute("SELECT * FROM Student_Quiz WHERE QuizExamID = %s AND StudentID = %s", (quizid, student_id))
                    student_rows = cursor.fetchall()
                    student_columns = [col[0] for col in cursor.description]
                    student_quiz_data = [dict(zip(student_columns, row)) for row in student_rows]
                    if len(student_quiz_data) == 0:
                        section['quizzes'][i]["student"] = {} 
                    else:
                        section['quizzes'][i]["student"] = student_quiz_data[0]
    except Exception as e:
        print("student_rows")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
def fetch_student_contests_in_course(course_id, student_id):
    contests = fetch_contests(course_id)
    try:
        with connection.cursor() as cursor:
            for i, contest in enumerate(contests):
                contestid = contest['contestexamid']
                cursor.execute("SELECT * FROM Student_Contest WHERE ContestExamID = %s AND StudentID = %s", (contestid, student_id))
                student_rows = cursor.fetchall()
                student_columns = [col[0] for col in cursor.description]
                student_quiz_data = [dict(zip(student_columns, row)) for row in student_rows]
                if len(student_quiz_data) == 0:
                    contests[i]["student"] = {}
                else:
                    contests[i]["student"] = student_quiz_data[0]
    except Exception as e:
        print("student_rows")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return contests
#################### Fetch HomeWorks To Students ####################

#################### Fetch HomeWorks ####################
def fetch_course_assignments(course_id, role, id):
    sections = fetch_raw_sections(course_id)
    if role == "student":
        sections = fetch_student_assignemnts_in_course(sections, id)
    elif role == "instructor":
        sections = fetch_assignments(sections)
    return sections
def fetch_course_quizzes(sections, role, id):
    if role == "student":
        sections = fetch_student_quizzes_in_course(sections, id)
    elif role == "instructor":
        sections = fetch_quizzes_overview(sections)
    return sections
def fetch_course_contests(course_id, role, id):
    if role == "student":
        contests = fetch_student_contests_in_course(course_id, id)
    elif role == "instructor":
        contests = fetch_contests(course_id)
    return contests
#################### Fetch HomeWorks ####################

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
def fetch_quizzes(sections): #To remove
    for i, outer_section in enumerate(sections):
        for j, inner_section in enumerate(outer_section):
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM QuizExam
                        WHERE SectionID = %s AND QuizExamID NOT IN (
                            SELECT QuizExamID FROM InstructorWhiteBoard AS i
                            WHERE i.AssignmentID IS NOT NULL
                        );
                    """, (inner_section['coursesectionid'],))
                    section_rows = cursor.fetchall()
                    section_columns = [col[0] for col in cursor.description]
                    sections[i][j]['quizzes'] = []
                    sections[i][j]['quizzes'].append([dict(zip(section_columns, row)) for row in section_rows])
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections

################# Fetch Package #################
def get_student_raw_data(student_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Student WHERE StudentId = %s", (student_id,))
        student_data_rows = cursor.fetchone()
        student_data_columns = [col[0] for col in cursor.description]
        student_data = dict(zip(student_data_columns, student_data_rows))
        del student_data["password"]
        return student_data
def get_instructor_raw_data(instructor_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Instructor WHERE InstructorId = %s", (instructor_id,))
        instructor_data_rows = cursor.fetchone()
        instructor_data_columns = [col[0] for col in cursor.description]
        instructor_data = dict(zip(instructor_data_columns, instructor_data_rows))
        del instructor_data["password"]
        return instructor_data
def fetch_contests(course_id):
    query = """
        SELECT * FROM ContestExam WHERE CourseID = %s AND ContestExamID NOT IN (
            SELECT ContestExamID FROM InstructorWhiteBoard AS i
            WHERE i.ContestExamID IS NOT NULL
        )
        ORDER BY ContestExamID ASC
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (course_id,))
            contests = cursor.fetchall()
            contests = [dict(zip([desc[0] for desc in cursor.description], contest)) for contest in contests]
            return contests
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def fetch_raw_courses(query, param, student_id = None):
    courses = []
    if not isinstance(param, tuple):
        param = (param,)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, param)
            rows = cursor.fetchall()
            if len(rows) == 0:
                return []
            columns = [col[0] for col in cursor.description]
            courses = [dict(zip(columns, row)) for row in rows]
            course_ids = [course['courseid'] for course in courses]
            if student_id is not None:
                for index, course in enumerate(courses):
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT OfferId, Discount FROM Offer WHERE StudentID = %s AND InstructorID = %s", (student_id,
                                courses[index]["topinstructorid"]))
                            rows = cursor.fetchall()
                            if rows is None:
                                courses[index]["offers"] = []
                            else:
                                cols = [col[0] for col in cursor.description]
                                offers = [dict(zip(cols, row)) for row in rows]
                                courses[index]["offers"] = offers
                    except Exception as e:
                        print("Error fetching course data: ", str(e))
            return (courses, course_ids)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def fetch_raw_sections(course_id):
    sections = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM CourseSection
                WHERE courseid = %s
                ORDER BY CourseSectionID ASC;
            """, (course_id,))
            section_rows = cursor.fetchall()
            section_columns = [col[0] for col in cursor.description]
            sections = [dict(zip(section_columns, row)) for row in section_rows]
            return sections
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def fetch_videos_overview(sections):
    for i, outer_section in enumerate(sections):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VideoID, VideoDuration, Title FROM Video WHERE CourseSectionID = %s ORDER BY VideoID ASC",
                    (outer_section['coursesectionid'],))
                section_rows = cursor.fetchall()
                # print("It is ok")
                section_columns = [col[0] for col in cursor.description]
                sections[i]['videos'] = []
                sections[i]["videos"] = [dict(zip(section_columns, row)) for row in section_rows]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
def fetch_quizzes_overview(sections):
    print(sections)
    for i, outer_section in enumerate(sections):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM QuizExam
                    WHERE SectionID = %s AND QuizExamID NOT IN (
                        SELECT QuizExamID FROM InstructorWhiteBoard AS i
                        WHERE i.QuizExamID IS NOT NULL
                    )
                    ORDER BY QuizExamID ASC;
                """, (outer_section['coursesectionid'],))
                section_rows = cursor.fetchall()
                section_columns = [col[0] for col in cursor.description]
                sections[i]['quizzes'] = []
                sections[i]['quizzes'] = [dict(zip(section_columns, row)) for row in section_rows]
                quizzes = sections[i]['quizzes']
                for j, quiz in enumerate(quizzes):
                    instructor = get_instructor_raw_data(quiz['instructorid'])
                    if isinstance(instructor, Response):
                        return instructor
                    del sections[i]['quizzes'][j]['instructorid']
                    sections[i]['quizzes'][j]['instructor'] = instructor
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
def fetch_single_video(videoId, student_id):
    try:
        with connection.cursor() as cursor:
            if student_id is not None:
                cursor.execute("""
                    SELECT v.*, COALESCE(vs.VideoProgress, 0) AS VideoProgress
                    FROM Video AS v 
                    LEFT JOIN Video_Student AS vs 
                    ON v.VideoID = vs.VideoID AND vs.StudentID = %s 
                    WHERE v.VideoID = %s;
                """, (student_id, videoId))
            else:
                cursor.execute("SELECT * FROM Video WHERE VideoId = %s", (videoId,))
            video_row = cursor.fetchone()
            print(video_row)
            if video_row is None:
                return Response({"error": "Video not found"}, status=status.HTTP_404_NOT_FOUND)
            video_columns = [col[0] for col in cursor.description]
            video = dict(zip(video_columns, video_row))
            return video
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def fetch_assignments(sections):
    for i, outer_section in enumerate(sections):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM Assignment AS a
                    WHERE CourseSectionID = %s AND a.AssignmentID NOT IN (
                        SELECT i.AssignmentID FROM InstructorWhiteBoard AS i
                        WHERE i.AssignmentID IS NOT NULL
                    )
                    ORDER BY AssignmentID ASC;
                """, (outer_section['coursesectionid'],))
                section_rows = cursor.fetchall()
                section_columns = [col[0] for col in cursor.description]
                sections[i]['assignment'] = []
                sections[i]["assignment"] = [dict(zip(section_columns, row)) for row in section_rows]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return sections
################# Fetch Package #################

def add_chat_rooms(student_id, course_id, top_instructor_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT InstructorID FROM Course_Instructor WHERE CourseID = %s", (course_id,))
            result = cursor.fetchall()
            instructor_ids = [row[0] for row in result]
        insert_query = """
            INSERT INTO Chat (StudentID, CourseID, InstructorID)
            VALUES (%s, %s, %s);
        """
        connection.cursor().execute(insert_query, (student_id, course_id, top_instructor_id))
        for instructor_id in instructor_ids:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(insert_query, (student_id, course_id, instructor_id))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
def add_chat_rooms_for_new_instructors(course_id, instructor_id):
    insert_query = """
        INSERT INTO Chat (StudentID, CourseID, InstructorID)
        SELECT StudentID, %s, %s 
        FROM Student_Course 
        WHERE CourseID = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(insert_query, (course_id, instructor_id, course_id))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
            print(quiz)
            returned_value = create_quiz(title=quiz['title'], sectionID=section_id, questions=quiz['questions'],
                quizDuration=quiz['quizDuration'], totalMarks=quiz['totalMarks'], passingMarks=quiz['passingMarks'], user_id=user_id, course_id=course_id, flag=True),
            if isinstance(returned_value, Response):
                quiz_messages.append(returned_value.data)
        for video in section_videos:
            video_title = video.get("title", None)
            video_duration = video.get('duration', 0)
            video = video.get('video', None)
            if video is not None:
                try:
                    video_file = decode_base64_to_file(video)
                    upload_result = cloudinary.uploader.upload(video_file, resource_type='video', format='mp4')
                    video_url = upload_result['secure_url']
                    create_video_query = """
                        INSERT INTO video (coursesectionid, title, videolink, VideoDuration)
                        VALUES (%s, %s, %s, %s);
                    """
                    with connection.cursor() as cursor:
                        cursor.execute(create_video_query, (section_id, video_title, video_url, convert_seconds_to_interval(video_duration)))
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
            fetch_quiz_for_whiteboard(whiteboard_items)
            fetch_instructor_for_whiteboard(whiteboard_items)
            return whiteboard_items
    except Exception as e:
        return (Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST))

def get_course_price(course_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Price FROM Course WHERE CourseID = %s", (course_id,))
            print("get_course_price")
            price = cursor.fetchone()[0]
            return float(price)
    except Exception as e:
        print("Error in price")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def get_student_current_balance(student_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Balance FROM Student WHERE StudentID = %s", (student_id,))
            result = cursor.fetchone()
            if result[0] is None:
                return None
            print("get_student_current_balance: ", result)
            return float(result[0])
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
def make_transaction(student_id, instructor_id, course_id, discount, offerId):
    query = """
        INSERT INTO Transactions (StudentID, InstructorID, Price, Discount)
        VALUES (%s, %s, %s, %s) RETURNING TransactionID;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Count(StudentID) FROM Student_Course WHERE CourseID = %s AND StudentID = %s", (course_id, student_id))
            if not bool(cursor.fetchone()[0]):
                course_price = get_course_price(course_id)
                print("course_price: ", course_price)
                print("discount: ", discount)
                price = ((100 - discount) / 100) * course_price
                print("jkjkjkjkjkjjk")
                balance = get_student_current_balance(str(student_id))
                if isinstance(balance, Response):
                    return balance
                if balance is None:
                    return Response({"error": "Error In Student Balance does not exist"},status=status.HTTP_400_BAD_REQUEST)
                print("price: ", price)
                print("balance: ", balance)
                if balance >= price:
                    print("Ddddddddddddddd")
                    try:
                        cursor.execute(query, (student_id, instructor_id, course_price, discount))
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                    print("kkkkkkkkkkkkkkkkkkk")
                    transaction_id = cursor.fetchone()[0]
                    print("llllllllllllllllll")
                    make_student_pay(student_id, price)
                    print("ooooooooooooooo")
                else:
                    return Response({"error": "student has no enough balance to enroll on this course"}, status=status.HTTP_400_BAD_REQUEST)
                if offerId is not None:
                    cursor.execute("DELETE FROM Offer WHERE OfferID = %s", (offerId,))
                return transaction_id
            else:
                return Response({"error": "student is already enrolled in this course"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return (Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST), False)

def check_if_private_course(courseID):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT SeenStatus FROM Course WHERE CourseID = %s", (courseID,))
            return cursor.fetchone()[0] == 'private'
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def enroll_student_on_course(student_id, courseID, discount = 0, offerId = None, flag = False):
    (top_instructor_id, _) = fetch_top_instructor_by_course(courseID)
    print("I will make transaction")
    returned_value = make_transaction(student_id, top_instructor_id, courseID, discount, offerId)
    print("I have finished transaction")
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
    sections = fetch_raw_sections(courseID)
    sections = fetch_assignments(sections)
    sections = fetch_quizzes_overview(sections)
    contests = fetch_contests(courseID)
    for contest in contests:
        add_contest_to_student(student_id, contest["contestexamid"])
    if isinstance(sections, Response):
        return sections
    assignmentIDs = []
    quizIDs = []
    for outer_section in sections:
        for assignment in outer_section["assignment"]:
            assignmentIDs.append(assignment['assignmentid'])

    for outer_section in sections:
        for quiz in outer_section["quizzes"]:
            quizIDs.append(quiz['quizexamid'])
    
    for assignmentID in assignmentIDs:
        returned_value = add_assignment_to_student(studentID=student_id, assignmentID=assignmentID)
        if isinstance(returned_value, Response):
            return returned_value

    for quizId in quizIDs:
        returned_value = add_quiz_to_student(studentID=student_id, quizId=quizId)
        if isinstance(returned_value, Response):
            return returned_value
    if flag:
        add_chat_rooms(student_id, courseID, top_instructor_id)
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
            cursor.execute("SELECT SenderStudentID, SenderInstructorID FROM Messages WHERE MessageID = %s", (message_id,))
            row = cursor.fetchall()
            row = row[0]
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

def get_instructor_courses(instructor_id, private=False):
    top_instructor_query = "SELECT * FROM course WHERE topinstructorid = %s ORDER BY CourseID ASC"
    if private:
        top_instructor_query = "SELECT * FROM course WHERE topinstructorid = %s WHERE SeenStatus = 'private' ORDER BY CourseID ASC"
    returned_value = fetch_raw_courses(query=top_instructor_query, param=instructor_id)
    if isinstance(returned_value, Response):
        return returned_value
    elif isinstance(returned_value, list):
        top_instructor_courses = returned_value
    else:
        top_instructor_courses = returned_value[0]
    non_top_instructor_query = """
        SELECT c.* 
        FROM course AS c INNER JOIN course_instructor AS ci
        ON c.CourseID = ci.CourseID
        WHERE instructorid = %s
    """
    if private:
        non_top_instructor_query = """
            SELECT c.* 
            FROM course AS c INNER JOIN course_instructor AS ci
            ON c.CourseID = ci.CourseID
            WHERE instructorid = %s AND c.SeenStatus = 'private'
        """
    returned_value = fetch_raw_courses(query=non_top_instructor_query, param=instructor_id)
    if isinstance(returned_value, Response):
        return returned_value
    elif isinstance(returned_value, list):
        non_top_instructor_courses = returned_value
    else:
        non_top_instructor_courses = returned_value[0]
    return (top_instructor_courses, non_top_instructor_courses)

def get_course_duration_by_courseid(course_id):
    query = """
        SELECT EXTRACT(epoch FROM Duration)
        FROM course
        WHERE CourseID = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (course_id,))
            return cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def get_course_duration_by_sectionid(section_id):
    query = """
        SELECT EXTRACT(epoch FROM c.Duration) FROM Course AS c
        INNER JOIN CourseSection AS cs
        ON cs.CourseID = c.CourseID
        WHERE cs.CourseSectionID = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (section_id,))
            return cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def get_courseid_from_sectionid(section_id):
    query = """
        SELECT CourseID FROM CourseSection WHERE CourseSectionID = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (section_id,))
            return cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def get_sectionid_from_videoid(videoid):
    query = """
        SELECT CourseSectionID FROM Video WHERE VideoID = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (videoid,))
            return cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def update_course_duration(course_id, duration):
    query = """
        UPDATE course
        SET Duration = %s
        WHERE CourseID = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (duration, course_id))
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def get_course_id_from_section_id(section_id):
    query = """
        SELECT c.CourseID FROM Course AS c
        INNER JOIN CourseSection AS cs
        ON cs.CourseID = c.CourseID
        WHERE cs.CourseSectionID = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (section_id,))
            return cursor.fetchone()[0]
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get_students_data_in_quizzes(quizzes):
    try:
        with connection.cursor() as cursor:
            for i, quiz in enumerate(quizzes):
                quizid = quiz['quizexamid']
                cursor.execute("SELECT * FROM Student_Quiz WHERE QuizExamID = %s", (quizid,))
                student_rows = cursor.fetchall()
                student_columns = [col[0] for col in cursor.description]
                student_quiz_data = [dict(zip(student_columns, row)) for row in student_rows]
                for j, student_quiz in enumerate(student_quiz_data):
                    student_quiz_data[j]['student_data'] = get_student_raw_data(student_quiz["studentid"])
                if len(student_quiz_data) == 0:
                    quizzes[i]["student"] = {} 
                else:
                    print("MUSTAAAAAAAAAAAAAAAAAAAAAAAARD")
                    quizzes[i]["student"] = student_quiz_data
    except Exception as e:
        print("student_rows")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def get_students_data_in_assignemnts(assignments):
    try:
        with connection.cursor() as cursor:
            for i, assignment in enumerate(assignments):
                assignmentid = assignment['assignmentid']
                cursor.execute("SELECT * FROM Student_Assignment WHERE AssignmentID = %s", (assignmentid,))
                student_rows = cursor.fetchall()
                student_columns = [col[0] for col in cursor.description]
                student_assignment_data = [dict(zip(student_columns, row)) for row in student_rows]
                for j, student_quiz in enumerate(student_assignment_data):
                    student_assignment_data[j]['student_data'] = get_student_raw_data(student_quiz["studentid"])
                if len(student_assignment_data) == 0:
                    assignments[i]["student"] = {}
                else:
                    assignments[i]["student"] = student_assignment_data
    except Exception as e:
        print("student_rows")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def get_students_data_in_contests(course_id):
    contests = fetch_contests(course_id)
    try:
        with connection.cursor() as cursor:
            for i, contest in enumerate(contests):
                contestid = contest['contestexamid']
                cursor.execute("SELECT * FROM Student_Contest WHERE ContestExamID = %s", (contestid,))
                student_rows = cursor.fetchall()
                student_columns = [col[0] for col in cursor.description]
                student_contests_data = [dict(zip(student_columns, row)) for row in student_rows]
                for j, student_contest in enumerate(student_contests_data):
                    student_contests_data[j]['student_data'] = get_student_raw_data(student_contest["studentid"])
                if len(student_contests_data) == 0:
                    contests[i]["student"] = {}
                else:
                    contests[i]["student"] = student_contests_data
    except Exception as e:
        print("student_rows")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return contests


def get_course_learning_time(course_id, student_id):
    query = """
        SELECT SUM((vs.VideoProgress / 100) * v.VideoDuration) FROM Video_Student AS vs
        INNER JOIN Video AS v
        ON vs.VideoID = v.VideoID
        WHERE vs.StudentID = %s AND vs.CourseID = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (student_id, course_id))
            result = cursor.fetchone()
            print("learning time: ", result)
            if result[0] is not None:
                return result[0].total_seconds()
            return 0
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
def get_courses_progress(student_id, course_id):
    returned_value = get_course_learning_time(course_id, student_id)
    course_duration = float(get_course_duration_by_courseid(course_id))
    print("course_duration: ", course_duration)
    print("course_progress: ", returned_value)
    print("///////////////////////////////////")
    progress = returned_value
    if course_duration != 0:
        progress /= course_duration
    return progress

class GetAppStatsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        num_students_query = """
            SELECT COUNT(*) FROM Student
        """
        num_instructors_query = """
            SELECT COUNT(*) FROM Instructor
        """
        num_courses_query = """
            SELECT COUNT(*) FROM Course
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(num_students_query)
                num_students = cursor.fetchone()[0]
                cursor.execute(num_instructors_query)
                num_instructors = cursor.fetchone()[0]
                cursor.execute(num_courses_query)
                num_courses = cursor.fetchone()[0]
                return Response({"num_students": num_students, "num_instructors": num_instructors, "num_courses": num_courses},
                    status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StartLiveQASession(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request, course_id):
        query = """
            SELECT Email FROM Student_Course AS sc INNER JOIN Student AS s
            ON sc.StudentID = s.StudentID
            WHERE CourseID = %s
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (course_id,))
                students = cursor.fetchall()
                if not students:
                    return Response({"error": "No students in the course"}, status=status.HTTP_400_BAD_REQUEST)
                students = [email[0] for email in students]
                send_email_qa(students, course_id)
                return Response({"message": students}, status=status.HTTP_200_OK)
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
        returned_value = get_instructor_courses(request.user['id'])
        if isinstance(returned_value, Response):
            return returned_value
        top_instructor_courses = returned_value[0]
        non_top_instructor_courses = returned_value[1]
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
                cursor.execute("SELECT * FROM QuizExam WHERE QuizExamId = %s", (quizID,))
                quiz_exam_rows = cursor.fetchone()
                if quiz_exam_rows is None:
                    return Response({"error": "QuizExam not found"}, status=status.HTTP_404_NOT_FOUND)
                quiz_exam = quiz_exam_rows
                quiz_exam_cols = [col[0] for col in cursor.description]
                quiz_exam_data = dict(zip(quiz_exam_cols, quiz_exam))
                cursor.execute(query, (quizID,))
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                questions = [dict(zip(columns, row)) for row in rows]
                instructor = get_instructor_raw_data(quiz_exam_data["instructorid"])
                quiz_exam_data["instructor"] = instructor
                del quiz_exam_data["instructorid"]

                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT * FROM Student_Quiz WHERE QuizExamID = %s", (quizID,))
                        data_rows = cursor.fetchall()
                        if len(data_rows) == 0:
                            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
                        data_cols = [col[0] for col in cursor.description]
                        data = [dict(zip(data_cols, row)) for row in data_rows]
                        print("klklklk")
                        for j, datum in enumerate(data):
                            data[j]["student"] = get_student_raw_data(datum["studentid"])
                            del data[j]["studentid"]
                        quiz_exam_data["data"] = data

                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                quiz = {
                    "Quiz": quiz_exam_data,
                    "Questions": questions
                }
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(quiz, status=status.HTTP_200_OK)
class GetContestExamView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, contestID):
        query = """
            SELECT q.* FROM Questions AS q INNER JOIN ContestExam AS qe
            ON q.ContestExamID = qe.ContestExamID
            WHERE qe.ContestExamID = %s
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM ContestExam WHERE ContestExamId = %s", (contestID,))
                contest_exam_rows = cursor.fetchone()
                if contest_exam_rows is None:
                    return Response({"error": "contestExam not found"}, status=status.HTTP_404_NOT_FOUND)
                contest_exam = contest_exam_rows
                contest_exam_cols = [col[0] for col in cursor.description]
                contest_exam_data = dict(zip(contest_exam_cols, contest_exam))
                cursor.execute(query, (contestID,))
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                questions = [dict(zip(columns, row)) for row in rows]
                instructor = get_instructor_raw_data(contest_exam_data["instructorid"])
                contest_exam_data["instructor"] = instructor
                del contest_exam_data["instructorid"]

                if request.auth == "instructor":
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT * FROM Student_Contest WHERE ContestExamID = %s", (contestID,))
                            data_rows = cursor.fetchall()
                            if len(data_rows) == 0:
                                return Response({"error": "contest not found"}, status=status.HTTP_404_NOT_FOUND)
                            data_cols = [col[0] for col in cursor.description]
                            data = [dict(zip(data_cols, row)) for row in data_rows]
                            print("klklklk")
                            for j, datum in enumerate(data):
                                data[j]["student"] = get_student_raw_data(datum["studentid"])
                                del data[j]["studentid"]
                            contest_exam_data["data"] = data
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                contest = {
                    "contest": contest_exam_data,
                    "Questions": questions
                }
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(contest, status=status.HTTP_200_OK)    
class GetStudentCourses(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def get(self, request):
        query = """
            SELECT * FROM student_course AS sc INNER JOIN course AS c 
            ON sc.courseid = c.courseid AND sc.studentid = %s
            ORDER BY PurchaseDate ASC;
        """
        returned_value = fetch_raw_courses(query=query, param=request.user["id"], student_id=request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        elif isinstance(returned_value, list):
            courses = returned_value
        else:
            courses = returned_value[0]  
        return Response(courses, status=status.HTTP_200_OK)

class FetchCategoriesView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM categories")
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                categories = [dict(zip(columns, row)) for row in rows]
                return Response(categories, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class GetUserPrivateCourses(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        if request.auth == "student":
            student_query = """
                SELECT c.* FROM Student_Course AS sc
                INNER JOIN Course AS c
                ON sc.courseid = c.courseid AND c.SeenStatus = 'private'
                WHERE sc.StudentID = %s
            """
            returned_value = fetch_raw_courses(query=student_query, param=request.user["id"])
            if isinstance(returned_value, Response):
                return returned_value
            return Response(returned_value[0], status=status.HTTP_200_OK)
        elif request.auth == "instructor":
            returned_value = get_instructor_courses(request.user['id'])
            if isinstance(returned_value, Response):
                return returned_value
            top_instructor_courses = returned_value[0]
            non_top_instructor_courses = returned_value[1]
            return Response({
                "top_instructor_courses": top_instructor_courses,
                "non_top_instructor_courses": non_top_instructor_courses
            }, status=status.HTTP_200_OK)
        

# to edit to be eligible for instructor and student
class GetStudentDataInCourseView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def get(self, request):
        student_id = request.data.get("student_id", None)
        course_id = request.data.get("course_id", None)
        if student_id is None or course_id is None:
            return Response({"error": "smth wrong in inserted data"}, status=status.HTTP_400_BAD_REQUEST)
        instructor_query = """
            SELECT COUNT(*)
            FROM Course AS c
            INNER JOIN Course_Instructor AS ci
            ON c.CourseID = ci.CourseID
            INNER JOIN Student_Course AS sc
            ON sc.CourseID = c.CourseID
            WHERE c.CourseID = %s AND (c.TopInstructorID = %s OR ci.InstructorID = %s) AND sc.StudentID = %s;
        """
        student_query = """
            SELECT vs.VideoProgress, v.Title AS VideoTitle,
            v.VideoID, cs.Title AS CourseSectionTitle, cs.CourseSectionID
            FROM CourseSection AS cs
            INNER JOIN Video AS v
            ON v.CourseSectionID = cs.CourseSectionID
            LEFT JOIN Video_Student AS vs
            ON v.VideoID = vs.VideoID AND vs.StudentID = %s
            ORDER BY cs.CourseSectionID, v.VideoID;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(instructor_query, (course_id, request.user["id"], request.user["id"], student_id))
                result = cursor.fetchone()[0]
                if result == 0:
                    return Response({"error": "You are not an instructor in this course or course does not exist or student is not in this course or does not exist"}, status=status.HTTP_403_FORBIDDEN)
                cursor.execute(student_query, (student_id,))
                student_data_rows = cursor.fetchall()
                student_data_columns = [col[0] for col in cursor.description]
                student_data = [dict(zip(student_data_columns, student_row)) for student_row in student_data_rows]
                sections = []
                for item in student_data:
                    section_id = item.get("coursesectionid") - 1
                    while len(sections) <= section_id:
                        sections.append([])
                    sections[section_id].append(item)
                cursor.execute("SELECT * FROM Student WHERE StudentId = %s", (student_id,))
                student_rows = cursor.fetchone()
                student_columns = [col[0] for col in cursor.description]
                student = dict(zip(student_columns, student_rows))
                return Response({
                    "student_data": student,
                    "student_data_in course": sections
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StudentEnrollmentView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        courseID = request.data.get("courseID", None)
        offerID = request.data.get("offerID", None)
        discount = request.data.get("discount", 0)
        if offerID is None and discount > 0 or offerID is not None and discount == 0:
            return Response({"error": "Invalid discount"}, status=status.HTTP_400_BAD_REQUEST)
        return enroll_student_on_course(request.user['id'], courseID, discount, offerID, False)

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
                for i, question in enumerate(questions):
                    if question['senderstudentid'] is not None:
                        student_data = get_student_raw_data(question['senderstudentid'])
                        del questions[i]['senderstudentid']
                        questions[i]['senderstudent'] = student_data
                    elif question['senderinstructorid'] is not None:
                        instructor_data = get_instructor_raw_data(question['senderinstructorid'])
                        del questions[i]['senderinstructorid']
                        questions[i]['senderinstructor'] = instructor_data

                cursor.execute(answers_query, (qaid, True))
                answer_rows = cursor.fetchall()
                answer_columns = [col[0] for col in cursor.description]
                answers = [dict(zip(answer_columns, row)) for row in answer_rows]
                for i, answer in enumerate(answers):
                    if answer['senderstudentid'] is not None:
                        student_data = get_student_raw_data(answer['senderstudentid'])
                        del answers[i]['senderstudentid']
                        answers[i]['senderstudent'] = student_data
                    elif answer['senderinstructorid'] is not None:
                        instructor_data = get_instructor_raw_data(answer['senderinstructorid'])
                        print("I am in instructor now")
                        del answers[i]['senderinstructorid']
                        answers[i]['senderinstructor'] = instructor_data


        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"questions": questions, "answers": answers}, status=status.HTTP_200_OK)
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
                for i, message in enumerate(messages):
                    if message['senderstudentid'] is not None:
                        student_data = get_student_raw_data(message['senderstudentid'])
                        del messages[i]['senderstudentid']
                        messages[i]['senderstudent'] = student_data
                    elif message['senderinstructorid'] is not None:
                        instructor_data = get_instructor_raw_data(message['senderinstructorid'])
                        del messages[i]['senderinstructorid']
                        messages[i]['senderinstructor'] = instructor_data
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
    permission_classes = [AllowAny]
    def delete(self, request):
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
                    return Response({"message": "Message deleted"}, status=status.HTTP_200_OK)
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
            passingMarks=passingMarks, user_id=request.user["id"], course_id=course_id, flag=top_instructor_id==request.user["id"])
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
        (topInstructorID, _) = fetch_top_instructor_by_course(courseID)
        flag = check_if_private_course(courseID)
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
        print("HERER")
        for instructor in instructor_list:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(get_id_query, (instructor,))
                    instructorID = cursor.fetchone()[0]
                    instructorsIDs.append(instructorID)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        for instructorID in instructorsIDs:
            if flag:
                add_chat_rooms_for_new_instructors(courseID, instructorID)
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
            return Response({"message": "Assignment Added"}, status=status.HTTP_200_OK)
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
            return Response({"message": "Assignment Added to whiteboard"}, status=status.HTTP_200_OK)
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
                cursor.execute("SELECT VideoLink, EXTRACT(epoch FROM VideoDuration) FROM Video WHERE VideoID = %s", (videoId,))
                videoLink, video_duration = cursor.fetchone()
                print(videoLink)
                if videoLink is None:
                    return Response({"error": "Video does not exist"}, status=status.HTTP_400_BAD_REQUEST)
                video_public_id = extract_public_id(videoLink[0])
                cloudinary.uploader.destroy(video_public_id)
                section_id = get_sectionid_from_videoid(videoid=videoId)
                if isinstance(section_id, Response):
                    return section_id
                course_id = get_course_id_from_section_id(section_id)
                if isinstance(course_id, Response):
                    return course_id
                course_duration = get_course_duration_by_courseid(course_id)
                if isinstance(course_duration, Response):
                    return course_duration
                new_set_duration = course_duration - video_duration
                update_course_duration(course_id=course_id, duration=convert_seconds_to_interval(new_set_duration))
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
    def put(self, request):
        quiz = request.data.get("quiz", None)
        if quiz is None:
            return Response({"error": "Quiz data is missing"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = update_quiz(data=quiz)
        if isinstance(returned_value, Response):
            return returned_value
        return Response({"message": "Quiz succesfully updated"}, status=status.HTTP_200_OK)
class UpdateAssignment(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def put(self, request):
        data = request.data
        if request.FILES:
            returned_value = update_assignment(data=data, FILES=request.FILES)
        else:
            returned_value = update_assignment(data=data)
        if isinstance(returned_value, Response):
            return returned_value
        return Response({"message": "Assignment succesfully updated"}, status=status.HTTP_200_OK)

class GetVideoView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, video_id):
        if request.auth == "student":
            video = fetch_single_video(video_id, request.user["id"])
        elif request.auth == "instructor":
            video = fetch_single_video(video_id, None)
        if isinstance(video, Response):
            return video
        return Response(video, status=status.HTTP_200_OK)

class UpdateCourse(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def put(self, request):
        course_id = request.data.get('courseId', None)
        title = request.data.get('title', None)
        description = request.data.get('description', None)
        categoryID = request.data.get("categoryID", None)
        seen_status = request.data.get("seen_status", None)
        price = request.data.get("price", None)
        requirements = request.data.get('requirements', [])
        duration = request.data.get('duration', "0")
        course_image = request.data.get('course_image', None)
        certificate = request.data.get('certificate', None)
        sections = request.data.get('sections', [])
        if course_id is None or title is None or description is None or categoryID is None or seen_status is None or price is None or requirements is None or duration is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        (top_instructor_id,_) = fetch_top_instructor_by_course(course_id)
        if top_instructor_id == request.user["id"]:
            update_query = """
                UPDATE Course
                SET 
                    Title = %s,
                    Description = %s,
                    TopInstructorID = %s,
                    CategoryID = %s,
                    SeenStatus = %s,
                    Duration = %s,
                    Price = %s,
                    Requirements = %s
                WHERE
                    CourseID = %s;
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(update_query, (title, description, request.user["id"],
                        categoryID, seen_status, convert_seconds_to_interval(duration), price, requirements, course_id))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if course_image is not None:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT courseimage FROM course WHERE courseid = %s", (course_id,))
                        image = cursor.fetchone()
                        if image is None:  # Handle case where no course image is found
                            return Response({"error": "Course image not found for the given course ID."}, status=status.HTTP_404_NOT_FOUND)
                        image_public_id = extract_public_id(image[0])
                        course_image_file = decode_base64_to_file(course_image)
                        upload_result = cloudinary.uploader.upload(course_image_file, public_id=image_public_id)
                        image_url = upload_result['secure_url']
                        query = """
                            UPDATE course
                            SET courseimage = %s
                            WHERE courseid = %s;
                        """ 
                        cursor.execute(query, (image_url, course_id))
                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            if certificate is not None:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT certificate FROM course WHERE courseid = %s", (course_id,))
                        image = cursor.fetchone()
                        if image is None:  # Handle case where no course image is found
                            return Response({"error": "Course certificate not found for the given course ID."}, status=status.HTTP_404_NOT_FOUND)
                        image_public_id = extract_public_id(image[0])
                        certificate_file = decode_base64_to_file(certificate)
                        upload_result = cloudinary.uploader.upload(certificate_file, public_id=image_public_id)
                        image_url = upload_result['secure_url']
                        query = """
                            UPDATE course
                            SET certificate = %s
                            WHERE courseid = %s;
                        """
                        cursor.execute(query, (image_url, course_id))
                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            for section in sections:
                sectionId = section.get("sectionId", None)
                returned_value = update_section(data=section, sectionID=sectionId)
                if isinstance(returned_value, Response):
                    return returned_value
            return Response({"message": "Course updated successfully"},status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not the top instructor of this course"}, status=status.HTTP_403_FORBIDDEN)

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
        course_id = None
        new_duration = 0
        for video in videos:
            section_id = video.get("section_id", None)
            if course_id is None:
                course_id = get_courseid_from_sectionid(section_id)
            video_title = video.get("title", None)
            video_duration = video.get('duration', 0)
            new_duration += video_duration
            print(video_duration)
            video = video.get('video', None)
            if section_id is None or video_title is None or video is None:
                return Response({"message": "Please provide all required fields"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                video_file = decode_base64_to_file(video)
                upload_result = cloudinary.uploader.upload(video_file, resource_type='video', format='mp4')
                video_url = upload_result['secure_url']
                create_video_query = """
                    INSERT INTO video (coursesectionid, title, videolink, VideoDuration)
                    VALUES (%s, %s, %s, %s)
                """
                with connection.cursor() as cursor:
                    cursor.execute(create_video_query, (section_id, video_title, video_url, convert_seconds_to_interval(video_duration)))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        old_course_duration = get_course_duration_by_sectionid(section_id)
        if isinstance(old_course_duration, Response):
            return old_course_duration
        set_duration = old_course_duration + new_duration
        returned_value = update_course_duration(course_id, convert_seconds_to_interval(set_duration))
        if isinstance(returned_value, Response):
            return returned_value
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
        discount = request.data.get("discount", None)
        passingMarks = request.data.get("passingMarks", None)
        if title is None or coureseId is None or questions is None or quizDuration is None or totalMarks is None or discount is None or passingMarks is None:
            return Response({"message": "Please provide all required fields"}, status=status.HTTP_400_BAD_REQUEST)
        (top_instructor_id, course_id) = fetch_top_instructor_by_course(coureseId)
        if isinstance(top_instructor_id, Response):
            return top_instructor_id
        returned_value = create_contest(title=title, courseId=coureseId, questions=questions, quizDuration=quizDuration, totalMarks=totalMarks,
            passingMarks=passingMarks, user_id=request.user["id"], discount=discount, flag=top_instructor_id==request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        contest_id = returned_value
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
        title = request.query_params.get("title", None)
        if title is None:
            return Response({"message": "Please provide all required fields"}, status=status.HTTP_400_BAD_REQUEST)
        title = f"%{title}%"
        if request.auth == "student":
            query = """
                SELECT * FROM Course
                WHERE Title ILIKE %s AND seenStatus = 'public' AND CourseID NOT IN (
                    SELECT CourseID FROM Student_Course WHERE StudentID = %s
                );
            """
            courses = fetch_raw_courses(query, (title, request.user["id"]), request.user["id"])
        else:
            query = """
                SELECT * FROM Course
                WHERE Title ILIKE %s AND seenStatus = 'public' AND TopInstructorID != %s AND CourseID NOT IN (
                    SELECT CourseID FROM Course_Instructor WHERE InstructorID = %s
                );
            """
            courses = fetch_raw_courses(query, (title, request.user["id"], request.user["id"]))    
        if isinstance(courses, Response):
            return courses
        elif isinstance(courses, tuple):
            req_courses = courses[0]
        elif isinstance(courses, list):
            req_courses = courses
        for i, course in enumerate(req_courses):
            req_courses[i]["instructor"] = get_instructor_raw_data(course["topinstructorid"])
            del req_courses[i]["topinstructorid"]
        return Response(req_courses, status=status.HTTP_200_OK)
class SearchByCategories(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        categories = request.query_params.getlist("categories", [])
        query = """
            SELECT * FROM Course WHERE CategoryID = %s AND seenStatus = 'public'
        """
        courses = []
        for category in categories:
            if request.auth == "student":
                returned_value = fetch_raw_courses(query, category, request.user["id"])
            else:
                returned_value = fetch_raw_courses(query, category)
            if isinstance(returned_value, Response):
                return returned_value
            elif isinstance(returned_value, list):
                courses.append(returned_value)
            elif isinstance(returned_value, tuple):
                req_courses = returned_value[0]
                for i, course in enumerate(req_courses):
                    req_courses[i]["instructor"] = get_instructor_raw_data(course["topinstructorid"])
                    del req_courses[i]["topinstructorid"]
                courses.append(req_courses)
        return Response(courses, status=status.HTTP_200_OK)      
class SearchByTitleAndCategories(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request):
        title = request.data.get("title", None)
        categories = request.data.get("categories", [])
        query = """
            SELECT * FROM Course WHERE CategoryID = %s AND Title ILIKE %s AND seenStatus = 'public';
        """
        courses = []
        for category in categories:
            if request.auth == "student":
                returned_value = fetch_raw_courses(query, category, request.user["id"])
            else:
                returned_value = fetch_raw_courses(query, category)
            if isinstance(returned_value, Response):
                return returned_value
            elif isinstance(returned_value, list):
                courses.append(returned_value)
            courses.append(returned_value[0])
        return Response(courses, status=status.HTTP_200_OK)      
class GetSingleCourse(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, course_id):
        query = "SELECT * FROM course WHERE courseid = %s"
        if request.auth == "student":
            courses = fetch_raw_courses(query, course_id, request.user["id"])
        else:
            courses = fetch_raw_courses(query, course_id)
        if isinstance(courses, Response):
            return courses
        elif isinstance(courses, list) and len(courses) == 0:
            return Response({"error": "course not found"}, status=status.HTTP_404_NOT_FOUND)
        req_course = courses[0][0]
        contests = fetch_course_contests(course_id, request.auth, request.user["id"])
        if isinstance(contests, Response):
            return contests
        req_course['contests'] = contests
        sections = fetch_raw_sections(course_id)
        if isinstance(sections, Response):
            return sections
        sections = fetch_videos_overview(sections)
        if isinstance(sections, Response):
            return sections
        sections = fetch_course_quizzes(sections, request.auth, request.user["id"])
        if isinstance(sections, Response):
            return sections
        assignments = fetch_course_assignments(course_id, request.auth, request.user["id"])
        if isinstance(assignments, Response):
            return assignments
        for i, section in enumerate(sections):
            sections[i]["assignments"] = assignments[i]
        req_course["sections"] = sections
        req_course["contests"] = contests
        return Response(req_course, status=status.HTTP_200_OK)

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
                is_student = True
                if request.auth == 'student':
                    cursor.execute("SELECT * FROM Transactions WHERE StudentID = %s", (request.user['id'],))
                elif request.auth == 'instructor':
                    cursor.execute("SELECT * FROM Transactions WHERE InstructorID = %s", (request.user['id'],))
                    is_student = False
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                transactions_data = [dict(zip(columns, row)) for row in rows]
                for i, data in enumerate(transactions_data):
                    cursor.execute("SELECT * FROM Student WHERE StudentID = %s", (data["studentid"],))
                    student_data = cursor.fetchone()
                    if student_data:
                        columns = [col[0] for col in cursor.description]
                        transactions_data[i]["student"] = dict(zip(columns, student_data))
                    cursor.execute("SELECT * FROM Instructor WHERE InstructorID = %s", (data["instructorid"],))
                    instructor_data = cursor.fetchone()
                    if instructor_data:
                        columns = [col[0] for col in cursor.description]
                        transactions_data[i]["instructor"] = dict(zip(columns, instructor_data))
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
        item = fetch_whiteboard_item(item_id)
        returned_value = delete_whiteboard_item(item_id)
        if isinstance(returned_value, Response):
            return returned_value
        print(item)
        if isinstance(item, Response):
            return item
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT StudentID FROM Student_Course WHERE CourseID = %s", (course_id,))
                studentsIDs = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if item['assignmentid'] is not None:
            for studentID in studentsIDs:
                print(studentID)
                returned_value = add_assignment_to_student(studentID=studentID, assignmentID=int(item['assignmentid']))
                if isinstance(returned_value, Response):
                    return returned_value
        elif item['quizexamid'] is not None:
            for studentID in studentsIDs:
                returned_value = add_quiz_to_student(studentID=studentID, quizId=int(item['quizexamid']))
                if isinstance(returned_value, Response):
                    return returned_value
        elif item['contestexamid'] is not None:
            for studentID in studentsIDs:
                returned_value = add_contest_to_student(studentID=studentID, contestId=int(item['contestexamid']))
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
        offerID = request.data.get("offerID", None)
        discount = request.data.get("discount", 0)
        if offerID is None and discount > 0 or offerID is not None and discount == 0:
            return Response({"error": "Invalid discount"}, status=status.HTTP_400_BAD_REQUEST)
        returned_value = check_if_private_course(course_id)
        if isinstance(returned_value, Response):
            return returned_value
        if returned_value:
            return enroll_student_on_course(request.user['id'], course_id, discount, offerID, True)
        else:
            return Response({"error": "Course is not private"}, status=status.HTTP_400_BAD_REQUEST)

class GetAssignmentView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, assignmentId):
        if request.auth == "instructor":
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM Assignment WHERE AssignmentID = %s", (assignmentId,))
                    assignment_rows = cursor.fetchone()
                    if assignment_rows is None:
                        return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
                    assignment_cols = [col[0] for col in  cursor.description]
                    assignment = dict(zip(assignment_cols, assignment_rows))
                    cursor.execute("SELECT * FROM Student_Assignment WHERE AssignmentID = %s", (assignmentId,))
                    data_rows = cursor.fetchall()
                    if len(data_rows) == 0:
                        return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
                    data_cols = [col[0] for col in cursor.description]
                    data = [dict(zip(data_cols, row)) for row in data_rows]
                    for i, datum in enumerate(data):
                        data[i]["student"] = get_student_raw_data(datum["studentid"])
                        del data[i]["studentid"]
                    return Response({
                        "assignment": assignment,
                        "students_data": data
                    }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif request.auth == "student":
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM Assignment WHERE AssignmentID = %s", (assignmentId,))
                    assignment_rows = cursor.fetchone()
                    if assignment_rows is None:
                        return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
                    assignment_cols = [col[0] for col in  cursor.description]
                    assignment = dict(zip(assignment_cols, assignment_rows))
                    cursor.execute("SELECT * FROM Student_Assignment WHERE AssignmentID = %s AND StudentID = %s", (assignmentId, request.user["id"]))
                    data_rows = cursor.fetchone()
                    if data_rows is None:
                        return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
                    data_cols = [col[0] for col in cursor.description]
                    data = dict(zip(data_cols, data_rows))
                    data["student"] = get_student_raw_data(data["studentid"])
                    del data["studentid"]
                    return Response({
                        "assignment": assignment,
                        "student_data": data
                    }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GetCourseAssignmentsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, course_id):
        returned_value = fetch_course_assignments(course_id, request.auth, request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        if request.auth == "instructor":
            for section in returned_value:
                for i, assignment in enumerate(section["assignment"]):
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT * FROM Student_Assignment WHERE AssignmentID = %s", (assignment["assignmentid"],))
                            data_rows = cursor.fetchall()
                            if len(data_rows) == 0:
                                return Response({"error": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
                            data_cols = [col[0] for col in cursor.description]
                            data = [dict(zip(data_cols, row)) for row in data_rows]
                            for j, datum in enumerate(data):
                                data[j]["student"] = get_student_raw_data(datum["studentid"])
                                del data[j]["studentid"]
                            section["assignment"][i]["data"] = data
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # result_sections = [course["sections"] for course in returned_value]
        return Response(returned_value, status=status.HTTP_200_OK)
class GetCourseQuizzesView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, course_id):
        returned_value = _fetch_course_quizzes(course_id, request.auth, request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        if request.auth == "instructor":
            for section in returned_value:
                for i, quiz in enumerate(section["quizzes"]):
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT * FROM Student_Quiz WHERE QuizExamID = %s", (quiz["quizexamid"],))
                            data_rows = cursor.fetchall()
                            if len(data_rows) == 0:
                                return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
                            data_cols = [col[0] for col in cursor.description]
                            data = [dict(zip(data_cols, row)) for row in data_rows]
                            print("klklklk")
                            for j, datum in enumerate(data):
                                data[j]["student"] = get_student_raw_data(datum["studentid"])
                                del data[j]["studentid"]
                            section["quizzes"][i]["data"] = data
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(returned_value, status=status.HTTP_200_OK)
class GetCourseContestsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, course_id):
        returned_value = fetch_course_contests(course_id, request.auth, request.user["id"])
        if isinstance(returned_value, Response):
            return returned_value
        if request.auth == "instructor":
            for i, contest in enumerate(returned_value):
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT * FROM Student_Contest WHERE ContestExamID = %s", (contest["contestexamid"],))
                        data_rows = cursor.fetchall()
                        if len(data_rows) == 0:
                            return Response({"error": "contest not found"}, status=status.HTTP_404_NOT_FOUND)
                        data_cols = [col[0] for col in cursor.description]
                        data = [dict(zip(data_cols, row)) for row in data_rows]
                        print("klklklk")
                        for j, datum in enumerate(data):
                            data[j]["student"] = get_student_raw_data(datum["studentid"])
                            del data[j]["studentid"]
                        returned_value[i]["data"] = data
                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(returned_value, status=status.HTTP_200_OK)

class MakeAnnouncementView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def post(self, request):
        announcement = request.data.get('announcement', None)
        course_id = request.data.get('course_id', None)
        if announcement is None or course_id is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT InstructorID FROM Course_Instructor WHERE CourseID = %s", (course_id,))
                course_instructor_ids = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if top_instructor_id != request.user['id'] and request.user['id'] not in course_instructor_ids:
            return Response({"error": "You are not an instructor in this course"}, status=status.HTTP_400_BAD_REQUEST)
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
    def put(self, request):
        announcement = request.data.get('announcement', None)
        course_id = request.data.get('course_id', None)
        announcement_id = request.data.get('announcement_id', None)
        if announcement is None or course_id is None or announcement_id is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT AnnouncerID FROM CourseAnnouncements WHERE AnnouncementID = %s", (announcement_id,))
                announcer_id = cursor.fetchone()
                if announcer_id is None:
                    return Response({"error": "Announcement not found"}, status=status.HTTP_400_BAD_REQUEST)
                announcer_id = announcer_id[0]
                print("announcer_id: ", announcer_id)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if top_instructor_id != request.user['id'] and request.user['id'] != announcer_id:
            return Response({"error": "You are not authorized to edit this announcement"}, status=status.HTTP_403_FORBIDDEN)
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
    permission_classes = [AllowAny]
    def get(self, request, course_id):
        # (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        # try:
        #     with connection.cursor() as cursor:
        #         cursor.execute("SELECT InstructorID FROM Course_Instructor WHERE CourseID = %s", (course_id,))
        #         course_instructor_ids = [row[0] for row in cursor.fetchall()]
        # except Exception as e:
        #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # if top_instructor_id != request.user['id'] and request.user['id'] not in course_instructor_ids:
        #     return Response({"error": "You are not an instructor in this course"}, status=status.HTTP_400_BAD_REQUEST)
        # returned_value = check_if_private_course(course_id)
        # if isinstance(returned_value, Response):
        #     return returned_value
        # if returned_value:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM CourseAnnouncements WHERE CourseID = %s;", (course_id,))
                    announcements_rows = cursor.fetchall()
                    announcements_cols = [col[0] for col in cursor.description]
                    announcements = [dict(zip(announcements_cols, row)) for row in announcements_rows]
                    for i, announcement in enumerate(announcements):
                        instructor_id = announcement["announcerid"]
                        cursor.execute("SELECT * FROM Instructor WHERE InstructorID = %s", (instructor_id,))
                        instructor_rows = cursor.fetchone()
                        instructor_cols = [col[0] for col in cursor.description]
                        instructor = dict(zip(instructor_cols, instructor_rows))
                        announcements[i]["announcer"] = instructor
                        del announcements[i]["announcerid"]
                    return Response(announcements, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # else:
        #     return Response({"error": "Course is not private"}, status=status.HTTP_400_BAD_REQUEST)
class DeleteAnnouncementView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def delete(self, request):
        announcement_id = request.data.get('announcement_id')
        course_id = request.data.get('course_id')
        (top_instructor_id, _) = fetch_top_instructor_by_course(course_id)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT AnnouncerID FROM CourseAnnouncements WHERE AnnouncementID = %s", (announcement_id,))
                print(announcement_id)
                announcer_id = cursor.fetchone()
                print(announcer_id)
                if announcer_id is None:
                    return Response({"error": "Announcement not found"}, status=status.HTTP_400_BAD_REQUEST)
                announcer_id = announcer_id[0]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if top_instructor_id != request.user['id'] and request.user['id'] != announcer_id:
            return Response({"error": "You are not authorized to delete this announcement"}, status=status.HTTP_403_FORBIDDEN)
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
        sections = fetch_raw_sections(course_id)
        temp_sections = copy.deepcopy(sections)
        # try:
        #     with connection.cursor() as cursor:
        #         cursor.execute("""
        #             SELECT CourseSectionID, Title FROM CourseSection
        #             WHERE courseid = %s;
        #         """, (course_id,))
        #         section_rows = cursor.fetchall()
        #         section_columns = [col[0] for col in cursor.description]
        #         sections = [dict(zip(section_columns, row)) for row in section_rows]
        # except Exception as e:
        #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
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
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT StudentID FROM Student_Course WHERE CourseID = %s", (course_id,))
                studentsIDs = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        students = []
        assignments = []
        quizzes = []
        contests = get_students_data_in_contests(course_id)
        temp_sections = fetch_quizzes_overview(temp_sections)
        temp_sections = fetch_assignments(temp_sections)
        for outer_section in temp_sections:
            section_quizzes = outer_section["quizzes"]
            section_assignments = outer_section["assignment"]
            get_students_data_in_quizzes(section_quizzes)
            get_students_data_in_assignemnts(section_assignments)
            quizzes.append(section_quizzes)
            assignments.append(section_assignments)
        for i, studentID in enumerate(studentsIDs):
            student_item = {}
            student_data = get_student_raw_data(studentID)
            if isinstance(student_data, Response):
                return student_data
            student_progress = get_courses_progress(student_id=studentID, course_id=course_id)
            if isinstance(returned_value, Response):
                return returned_value
            student_item["student_data"] = student_data
            student_item["student_progress"] = student_progress
            students.append(student_item)

        return Response({
            "total_students": total_students,
            "students_progress": students,
            "assignments": assignments,
            "contests": contests,
            "quizzes": quizzes,
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
            return Response({"error": "Course ID and review are required"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO FeedBack_Reviews (CourseID, InstructorID, Review, Rating, StudentId)
            VALUES (%s, %s, %s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (course_id, None, review, rating, request.user["id"]))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        rating_query = """
            SELECT CAST(SUM(Rating) AS FLOAT) / COUNT(*) FROM FeedBack_Reviews WHERE CourseId = %s
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(rating_query, (course_id,))
                rating = cursor.fetchone()[0]
                cursor.execute("UPDATE Course SET Rating = %s WHERE CourseId = %s", (rating, course_id))
                return Response({"message": "Feedback review added successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AddFeedbackReviewToInstructorView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        rating = request.data.get('rating', None)
        instructor_id = request.data.get('instructor_id', None)
        review = request.data.get('review', None)
        if instructor_id is None or review is None or rating is None:
            return Response({"error": "Instructor ID and review are required"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO FeedBack_Reviews (CourseID, InstructorID, Review, Rating, StudentId)
            VALUES (%s, %s, %s, %s, %s);
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (None, instructor_id, review, rating, request.user["id"]))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        rating_query = """
            SELECT CAST(SUM(Rating) AS FLOAT) / COUNT(*) FROM FeedBack_Reviews WHERE InstructorID = %s
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(rating_query, (instructor_id,))
                rating = cursor.fetchone()[0]
                print(rating)
                cursor.execute("UPDATE Instructor SET Rating = %s WHERE InstructorId = %s", (rating, instructor_id))
                print("THEN")
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
        course_id = request.data.get("course_id", None)
        instructor_id = request.data.get("instructor_id", None)
        if ReviewID is None or review is None or rating is None or (course_id is None and instructor_id is None) or (course_id is not None and instructor_id is not None):
            return Response({"error": "smthing wrong in passed data"}, status=status.HTTP_400_BAD_REQUEST)
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
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if instructor_id is not None:
            rating_query = """
                SELECT CAST(SUM(Rating) AS FLOAT) / COUNT(*) FROM FeedBack_Reviews WHERE InstructorID = %s
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(rating_query, (instructor_id,))
                    rating = cursor.fetchone()[0]
                    cursor.execute("UPDATE Instructor SET Rating = %s WHERE InstructorId", (rating, instructor_id))
                    return Response({"message": "Feedback review added successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif student_id is not None:
            rating_query = """
                SELECT CAST(SUM(Rating) AS FLOAT) / COUNT(*) FROM FeedBack_Reviews WHERE CourseId = %s
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(rating_query, (course_id,))
                    rating = cursor.fetchone()[0]
                    cursor.execute("UPDATE Course SET Rating = %s WHERE CourseId = %s", (rating,course_id))
                    return Response({"message": "Feedback review added successfully"}, status=status.HTTP_200_OK)
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
                reviews_rows = cursor.fetchall()
                reviews_cols = [col[0] for col in cursor.description]
                reviews = [dict(zip(reviews_cols, row)) for  row in reviews_rows]
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
                reviews_rows = cursor.fetchall()
                reviews_cols = [col[0] for col in cursor.description]
                reviews = [dict(zip(reviews_cols, row)) for  row in reviews_rows]
                return Response({"reviews": reviews}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubmitQuizView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        quizId = request.data.get("quizId", None)
        pass_status = request.data.get("pass", None)
        grade = request.data.get("grade", None)
        if quizId is None or pass_status is None or grade is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        update_query = """
            UPDATE Student_Quiz 
            SET Pass = %s, Grade = %s, Status = %s
            WHERE QuizExamID = %s AND StudentID = %s
        """
        if pass_status == True:
            _status = "passed"
        else:
            _status = "failed"
        try:
            with connection.cursor() as cursor:
                cursor.execute(update_query, (pass_status, grade, _status, quizId, request.user["id"]))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Quiz submitted successfully"}, status=status.HTTP_200_OK)
class SubmitContestView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def post(self, request):
        contestId = request.data.get("contestId", None)
        pass_status = request.data.get("pass", None)
        grade = request.data.get("grade", None)
        discount = request.data.get("discount", None)
        if contestId is None or pass_status is None or grade is None or discount is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        response_message = {}
        update_query = """
            UPDATE Student_Contest 
            SET Pass = %s, Grade = %s, Status = %s
            WHERE ContestExamID = %s AND StudentID = %s
        """
        if pass_status == True:
            _status = "passed"
        else:
            _status = "failed"
        try:
            with connection.cursor() as cursor:
                cursor.execute(update_query, (pass_status, grade, _status, contestId, request.user["id"]))
                response_message["message"] = "Quiz submitted successfully"
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD)
        if pass_status == True:
            make_offer_query = """
                INSERT INTO Offer (InstructorID, StudentID, Discount)
                VALUES (%s, %s, %s);
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT CourseID FROM ContestExam WHERE ContestExamID = %s", (contestId,))
                    course_id = cursor.fetchone()[0]
                    (top_instructor_id,_) = fetch_top_instructor_by_course(course_id)
                    cursor.execute(make_offer_query, (top_instructor_id, request.user["id"], discount))
                    response_message["offer"] = "Offer made successfully"
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_message["offer"] = "eng7 el2wl y7beby"
        return Response(response_message, status=status.HTTP_200_OK)

def _fetch_course_quizzes(course_id, role, id):
    try:
        with connection.cursor() as cursor:
            sections = fetch_raw_sections(course_id)
            sections = fetch_course_quizzes(sections, role, id)
            if isinstance(sections, Response):
                return sections
            return sections
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

# def fetch_courses(query, param, student_id = None):
#     courses = []
#     if not isinstance(param, tuple):
#         param = (param,)
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute(query, param)
#             rows = cursor.fetchall()
#             columns = [col[0] for col in cursor.description]
#             courses = [dict(zip(columns, row)) for row in rows]
#             course_ids = [course['courseid'] for course in courses]
#             sections = []
#             contests = []
#             for i, course_id in enumerate(course_ids):
#                 if student_id is not None:
#                     returned_value = get_last_watched_video_course(student_id)
#                     if isinstance(returned_value, Response):
#                         return returned_value
#                     courses[i]['last_watched_video'] = returned_value
#                 cursor.execute("""
#                     SELECT * FROM CourseSection
#                     WHERE courseid = %s;
#                 """, (course_id,))
#                 section_rows = cursor.fetchall()
#                 section_columns = [col[0] for col in cursor.description]
#                 sections.append([dict(zip(section_columns, row)) for row in section_rows])
#                 contests.append(fetch_contests(course_id))
#             #////////////////////////////////////////Fetch Contests/////////////////////////////////////////#
#             if isinstance(contests, Response):
#                 return contests
#             #////////////////////////////////////////Fetch Quizzes/////////////////////////////////////////#
#             sections = fetch_quizzes(sections)
#             if isinstance(sections, Response):
#                 return sections
#             #////////////////////////////////////////Fetch Videos/////////////////////////////////////////#
#             sections = fetch_videos(sections, student_id)
#             if isinstance(sections, Response):
#                 return sections
#             #////////////////////////////////////////Fetch Assignment/////////////////////////////////////////#
#             sections = fetch_assignments(sections)
#             if isinstance(sections, Response):
#                 return sections
#             data = []
#             for i in range(len(courses)):
#                 temp_data = {}
#                 temp_data = courses[i]
#                 temp_data['contests'] = contests[i]
#                 temp_data['sections'] = sections[i]
#                 data.append(temp_data)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#     return data

# def fetch_course_assignments(course_id, role):
#     courses = []
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT * FROM Course WHERE CourseID = %s", (course_id,))
#             row = cursor.fetchone()
#             columns = [col[0] for col in cursor.description]
#             courses = dict(zip(columns, row))
#             course_ids = [course['courseid'] for course in courses]
#             sections = []
#             for i, course_id in enumerate(course_ids):
#                 cursor.execute("""
#                     SELECT * FROM CourseSection
#                     WHERE courseid = %s;
#                 """, (course_id,))
#                 section_rows = cursor.fetchall()
#                 section_columns = [col[0] for col in cursor.description]
#                 sections.append([dict(zip(section_columns, row)) for row in section_rows])
#             #////////////////////////////////////////Fetch Assignment/////////////////////////////////////////#
#             print(role)
#             if role == "student":
#                 sections = fetch_student_assignemnts_in_course(sections)
#             elif role == "instructor":
#                 sections = fetch_assignments(sections)
#             if isinstance(sections, Response):
#                 return sections
#             data = []
#             for i in range(len(courses)):
#                 temp_data = {}
#                 temp_data = courses[i]
#                 temp_data['sections'] = sections[i]
#                 data.append(temp_data)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#     return data