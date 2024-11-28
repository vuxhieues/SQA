import os
from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from django.db import connection
import cloudinary.uploader
from authenticate import GenerateTokens, CustomTokenAuthentication, CustomRefreshAuthentication
from django.template import loader
from django.core.mail import send_mail
from django.utils.html import strip_tags
from permission import IsInstructor, IsStudent
# Create your views here.

class ChangeDB(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        DROP_QUERY = """
            -- Drop custom types first
            DROP TYPE IF EXISTS AssignmentStatus CASCADE;
            DROP TYPE IF EXISTS CourseStatus CASCADE;
            DROP TYPE IF EXISTS ExamType CASCADE;

            -- Drop tables in reverse order of creation to avoid dependency issues
            DROP TABLE IF EXISTS FeedBack_Reviews CASCADE;
            DROP TABLE IF EXISTS InstructorWhiteBoard CASCADE;
            DROP TABLE IF EXISTS Statistics CASCADE;
            DROP TABLE IF EXISTS Transactions CASCADE;
            DROP TABLE IF EXISTS Student_Assignment CASCADE;
            DROP TABLE IF EXISTS CourseAnnouncements CASCADE;
            DROP TABLE IF EXISTS Assignment CASCADE;
            DROP TABLE IF EXISTS Questions CASCADE;
            DROP TABLE IF EXISTS ContestExam CASCADE;
            DROP TABLE IF EXISTS QuizExam CASCADE;
            DROP TABLE IF EXISTS Messages CASCADE;
            DROP TABLE IF EXISTS Chat CASCADE;
            DROP TABLE IF EXISTS QA CASCADE;
            DROP TABLE IF EXISTS Video CASCADE;
            DROP TABLE IF EXISTS CourseSection CASCADE;
            DROP TABLE IF EXISTS Student_Course CASCADE;
            DROP TABLE IF EXISTS Course_Instructor CASCADE;
            DROP TABLE IF EXISTS Course CASCADE;
            DROP TABLE IF EXISTS Student CASCADE;
            DROP TABLE IF EXISTS Instructor CASCADE;
            DROP TABLE IF EXISTS Categories CASCADE;
            DROP TABLE IF EXISTS Video_Student CASCADE;
        """
        NEW_QUERY = """
            CREATE TABLE Categories (
                CategoryID SERIAL PRIMARY KEY,
                CategoryText VARCHAR(100),
                NumOfCourses INT DEFAULT 0
            );

            CREATE TABLE Instructor (
                InstructorID BIGSERIAL PRIMARY KEY NOT NULL,
                InstructorName VARCHAR(100) NOT NULL,
                Email VARCHAR(127) UNIQUE NOT NULL CHECK (Email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
                Username VARCHAR(255) UNIQUE NOT NULL,
                Password VARCHAR(255) NOT NULL,
                ProfilePic TEXT DEFAULT NULL,
                BIO TEXT,
                Rating INT DEFAULT 0 CHECK (Rating >= 0 AND Rating <= 5),
                CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                SocialMediaAccount TEXT[],
                Balance Decimal(10,2) DEFAULT 0
            );

            CREATE TABLE Student (
                StudentID BIGSERIAL PRIMARY KEY NOT NULL,
                StudentName VARCHAR(100) NOT NULL,
                Email VARCHAR(127) UNIQUE NOT NULL CHECK (Email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
                Username VARCHAR(255) UNIQUE NOT NULL,
                Password VARCHAR(255) NOT NULL,
                ProfilePic TEXT DEFAULT NULL,
                CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                Balance Decimal(10,2) DEFAULT 0
            );

            CREATE TYPE CourseStatus AS ENUM ('public', 'private');

            CREATE TABLE Course (
                CourseID SERIAL PRIMARY KEY NOT NULL,
                Title VARCHAR(100) NOT NULL,
                Description TEXT NOT NULL,
                TopInstructorID INT REFERENCES Instructor(InstructorID)
                    ON DELETE CASCADE,
                CategoryID INT REFERENCES Categories(CategoryID) 
                    ON DELETE CASCADE,
                SeenStatus CourseStatus, --public or private
                Duration INTERVAL NOT NULL DEFAULT INTERVAL '0',
                CreatedAt TIMESTAMP Default CURRENT_TIMESTAMP,
                Price Decimal(8,2) CHECK (Price >= 0) NOT NULL,
                Rating INT DEFAULT 0 CHECK (Rating >= 0 AND Rating <= 5),
                Requirements TEXT[],
                CourseImage TEXT DEFAULT NULL,
                Certificate TEXT DEFAULT NULL --link of the certificate image
            );

            CREATE TABLE Course_Instructor (
                CourseID INT,
                InstructorID INT,
                PRIMARY KEY (CourseID, InstructorID),
                FOREIGN KEY (CourseID) REFERENCES Course(CourseID) ON DELETE CASCADE,
                FOREIGN KEY (InstructorID) REFERENCES Instructor(InstructorID) ON DELETE CASCADE
            );

            CREATE TABLE Student_Course (
                CourseID INT NOT NULL,
                StudentID INT NOT NULL,
                PurchaseDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                StudentProgress DECIMAL(3,1) DEFAULT 0,
                PRIMARY KEY (CourseID, StudentID),
                FOREIGN KEY (CourseID) REFERENCES Course(CourseID)
                    ON DELETE CASCADE,
                FOREIGN KEY (StudentID) REFERENCES Student(StudentID)
                    ON DELETE CASCADE
            );

            CREATE TABLE CourseSection (
                CourseSectionID SERIAL PRIMARY KEY,
                CourseID INT REFERENCES Course(CourseID) ON DELETE CASCADE,
                Title VARCHAR(100) NOT NULL,
                Duration INTERVAL DEFAULT INTERVAL '0'
            );

            CREATE TABLE Video (
                VideoID BIGSERIAL PRIMARY KEY,
                CourseSectionID INT REFERENCES CourseSection(CourseSectionID)
                    ON DELETE CASCADE NOT NULL,
                VideoLink TEXT NOT NULL,
                VideoDuration INTERVAL NOT NULL DEFAULT INTERVAL '0',
                Title VARCHAR(100) NOT NULL
            );

            CREATE TABLE Video_Student (
                VideoID INT REFERENCES Video(VideoID) ON DELETE CASCADE,
                StudentID INT REFERENCES Student(StudentID) ON DELETE CASCADE,
                CourseID INT REFERENCES Course(CourseID) ON DELETE CASCADE,
                VideoProgress DECIMAL(4,2) CHECK (VideoProgress >= 0 AND VideoProgress <= 100) DEFAULT 0,
                CreatedAt TIMESTAMP Default CURRENT_TIMESTAMP,
                PRIMARY KEY (VideoID, StudentID)
            );

            CREATE TABLE QA (
                QAID SERIAL PRIMARY KEY,
                VideoID INT REFERENCES Video(VideoID)
                    ON DELETE CASCADE NOT NULL
            );

            CREATE TABLE Chat (
                ChatID BIGSERIAL PRIMARY KEY,
                StudentID INT REFERENCES Student(StudentID) NOT NULL,
                CourseID INT REFERENCES Course(CourseID) NOT NULL,
                InstructorID INT REFERENCES Instructor(InstructorID) NOT NULL,
                UNIQUE (StudentID, CourseID, InstructorID)
            );

            CREATE TABLE Messages (
                MessageID SERIAL PRIMARY KEY NOT NULL,
                MessageText TEXT NOT NULL,
                isAnswer BOOLEAN NOT NULL, -- true -> answer, false -> question
                AnswerTo INT REFERENCES Student(StudentID) ON DELETE SET NULL,
                SenderStudentID INT REFERENCES Student(StudentID) ON DELETE SET NULL,
                SenderInstructorID INT REFERENCES Instructor(InstructorID) ON DELETE SET NULL,
                QAID INT REFERENCES QA(QAID) ON DELETE CASCADE,
                ChatID INT REFERENCES Chat(ChatID) ON DELETE CASCADE,
                CreatedAt TIMESTAMP Default CURRENT_TIMESTAMP,
                CHECK (
                    (QAID IS NOT NULL AND ChatID IS NULL) OR
                    (QAID IS NULL AND ChatID IS NOT NULL)
                )
            );

            CREATE TYPE ExamType AS ENUM ('quiz', 'contest');

            CREATE TABLE QuizExam (
                QuizExamID BIGSERIAL PRIMARY KEY,
                Title TEXT,
                SectionID INT REFERENCES CourseSection(CourseSectionID) ON DELETE CASCADE NOT NULL,
                InstructorID INT REFERENCES Instructor(InstructorID) ON DELETE CASCADE,
                ExamKind ExamType DEFAULT 'quiz',
                Duration INTERVAL,
                TotalMarks DECIMAL(10, 2),
                PassingMarks DECIMAL(10, 2),
                CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE ContestExam (
                ContestExamID BIGSERIAL PRIMARY KEY,
                Title TEXT,
                CourseID INT REFERENCES Course(CourseID) ON DELETE CASCADE NOT NULL,
                InstructorID INT REFERENCES Instructor(InstructorID) ON DELETE CASCADE NOT NULL,
                ExamKind ExamType DEFAULT 'contest',
                Duration INTERVAL,
                TotalMarks DECIMAL(10, 2),
                PassingMarks DECIMAL(10, 2),
                CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE Questions (
                QuestionID BIGSERIAL PRIMARY KEY,
                QuizExamID INT REFERENCES QuizExam(QuizExamID) ON DELETE CASCADE,
                ContestExamID INT REFERENCES ContestExam(ContestExamID) ON DELETE CASCADE,
                QuestionText TEXT NOT NULL,
                Choices TEXT[],
                CorrectAnswerIndex INT,
                CHECK (
                    (QuizExamID IS NOT NULL AND ContestExamID IS NULL) OR
                    (ContestExamID IS NOT NULL AND QuizExamID IS NULL)
                )
            );

            CREATE TYPE AssignmentStatus AS ENUM ('pending', 'submitted', 'graded', 'passed', 'failed');

            CREATE TABLE Assignment (
                AssignmentID BIGSERIAL PRIMARY KEY,
                Title VARCHAR(100) NOt NULL,
                Description TEXT NOT NULL,
                CourseSectionID INT REFERENCES CourseSection(CourseSectionID) ON DELETE CASCADE,
                MaxMarks INT,
                PassingMarks INT,
                FileAttched TEXT, -- link to file attached
                CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE CourseAnnouncements (
                AnnouncementID BIGSERIAL PRIMARY KEY,
                AnnouncerID INT REFERENCES Instructor(InstructorID) ON DELETE SET NULL,
                CourseID INT REFERENCES Course(CourseID) ON DELETE CASCADE NOT NULL,
                Announcement TEXT
            );

            CREATE TABLE Student_Assignment (
                StudentAssignmentID BIGSERIAL PRIMARY KEY,
                StudentID INT REFERENCES Student(StudentID) ON DELETE CASCADE,
                AssignmentID INT REFERENCES Assignment(AssignmentID) ON DELETE CASCADE,
                SubmissionLink TEXT, -- Link to submitted assignment file, if applicable
                Grade DECIMAL(5,2), -- Grade achieved on the assignment
                Status AssignmentStatus DEFAULT 'pending',
                SubmissionDate TIMESTAMP,
                PassFail BOOLEAN -- true -> pass
            );

            CREATE TABLE Transactions (
                TransactionID BIGSERIAL PRIMARY KEY,
                StudentID INT REFERENCES Student(StudentID),
                InstructorID INT REFERENCES Instructor(InstructorID),
                Amount DECIMAL(10,2),
                ExecutedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- CREATE TABLE Statistics (
            -- 	CourseID INT REFERENCES Course(CourseID),
            -- 	InstructorID INT REFERENCES Instructor(InstructorID),
            -- 	StudentCount INT,
            -- 	CompletionRate DECIMAL(4,2),
            -- 	AverageGrades DECIMAL(10,2)
            -- );

            CREATE TABLE InstructorWhiteBoard (
                InstructorWhiteBoardID BIGSERIAL PRIMARY KEY,
                InstructorID INT REFERENCES Instructor(InstructorID),
                CourseID INT REFERENCES Course(CourseID),
                AssignmentID INT REFERENCES Assignment(AssignmentID) ON DELETE CASCADE,
                QuizExamID INT REFERENCES QuizExam(QuizExamID) ON DELETE CASCADE,
                ContestExamID INT REFERENCES ContestExam(ContestExamID) ON DELETE CASCADE,
                CHECK (
                    (QuizExamID IS NOT NULL AND ContestExamID IS NULL AND AssignmentID IS NULL) OR
                    (ContestExamID IS NOT NULL AND QuizExamID IS NULL AND AssignmentID IS NULL) OR
                    (ContestExamID IS NULL AND QuizExamID IS NULL AND AssignmentID IS NOT NULL)
                )
            );
            -- revise below table
            CREATE TABLE FeedBack_Reviews (
                ReviewID BIGSERIAL PRIMARY KEY,
                CourseID INT REFERENCES Course(CourseID),
                InstructorID INT REFERENCES Instructor(InstructorID),
                Rating DECIMAL(3,2),
                Review TEXT,
                CHECK (
                    (CourseID IS NOT NULL AND InstructorID IS NULL) OR
                    (CourseID IS NULL AND InstructorID IS NOT NULL)
                )
            );
        """
        try:
            connection.cursor().execute(DROP_QUERY)
            connection.cursor().execute(NEW_QUERY)
            print("Dropped existing tables")
        except Exception as e:
            print(f"Failed to drop existing tables: {e}")
            return Response({"message": "Failed to drop existing tables"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({}, status=status.HTTP_200_OK)



class SignUpAsInstructorView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        name = request.data.get("name", None)
        email = request.data.get("email", None)
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        Bio = request.data.get("Bio", "")
        SocialMedia = request.data.getlist("SocialMedia[]", []) # shoulda altered in production
        image = request.FILES.get('image', None)
        if name is None or email is None or username is None or password is None:
            return Response({
                "error": "smth wrong in inserted data",
            }, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO instructor (instructorname, email, username, password, bio, socialmediaaccount)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING instructorid;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (name, email, username, make_password(password), Bio, SocialMedia))
                instructor_id = cursor.fetchone()[0]
        except Exception as e:
            return Response({"errors": str(e),}, status=status.HTTP_400_BAD_REQUEST)
        if image is not None:
            try:
                upload_result = cloudinary.uploader.upload(image)
                image_url = upload_result['secure_url']
                query = """
                    UPDATE instructor
                    SET profilepic = %s
                    WHERE instructorid = %s;
                """
                print(image_url, instructor_id)
                with connection.cursor() as cursor:
                    cursor.execute(query, (image_url, instructor_id))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Instructor created successfully",}, status=status.HTTP_201_CREATED)
class GetStudentData(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def get(self, request, student_id):
        query = """
            SELECT Count(sc.CourseID) FROM Student_Course AS sc
            INNER JOIN Course_Instructor AS ci ON sc.CourseID = ci.CourseID
            WHERE sc.StudentID = %s AND ci.InstructorID = %s
        """
        query1 = """
            SELECT Count(sc.CourseID) FROM Student_Course AS sc
            INNER JOIN Course AS c ON sc.CourseID = c.CourseID
            WHERE sc.StudentID = %s AND c.TopInstructorID = %s
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (student_id, request.user['id']))
                count0 = cursor.fetchone()[0]
                cursor.execute(query1, (student_id, request.user['id']))
                count1 = cursor.fetchone()[0]
                if bool(count0) or bool(count1):
                    cursor.execute("SELECT * FROM Student WHERE StudentID = %s", (student_id,))
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    student_data = dict(zip(columns, rows[0]))
                    del student_data['password']
                    return Response({"student_data": student_data}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Student is not enrolled in any of this instructor course"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class SignUpAsStudentView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        name = request.data.get("name", None)
        email = request.data.get("email", None)
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        image = request.FILES.get('image', None)
        # Start Check Data validation
        if name is None or email is None or username is None or password is None:
            return Response({
                "error": "smth wrong in inserted data",
            }, status=status.HTTP_400_BAD_REQUEST)
        # End Check Data validation
        query = """
            INSERT INTO student (studentname, email, username, password)
            VALUES (%s, %s, %s, %s) RETURNING studentid;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (name, email, username, make_password(password)))
                student_id = cursor.fetchone()[0]
        except Exception as e:
            return Response({"errors": str(e),}, status=status.HTTP_400_BAD_REQUEST)
        if image is not None:
            try:
                upload_result = cloudinary.uploader.upload(image)
                image_url = upload_result['secure_url']
                query = """
                    UPDATE Student
                    SET profilepic = %s
                    WHERE studentid = %s;
                """
                print(image_url, student_id)
                with connection.cursor() as cursor:
                    cursor.execute(query, (image_url, student_id))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Student created successfully",}, status=status.HTTP_201_CREATED)
class SignInInstructorView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        # Start Check Data validation
        if username is None or password is None:
            return Response({
                "error": "smth wrong in inserted data",
            }, status=status.HTTP_400_BAD_REQUEST)
        print(username)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM instructor WHERE username = %s", (username,))
                instructor_temp_data = cursor.fetchall()
                if len(instructor_temp_data) == 0:
                    return Response({"error": "instructor not found",}, status=status.HTTP_404_NOT_FOUND)
                instructor_data = {
                    "id": instructor_temp_data[0][0],
                    "name": instructor_temp_data[0][1],
                    "email": instructor_temp_data[0][2],
                    "username": instructor_temp_data[0][3],
                    "password": instructor_temp_data[0][4],
                    "profilepic": instructor_temp_data[0][5],
                    "bio": instructor_temp_data[0][6],
                    "rating": instructor_temp_data[0][7],
                    "createdAt": instructor_temp_data[0][8],
                    "social_media": instructor_temp_data[0][9],
                }
        except Exception as e:
            return Response({"error": str(e),}, status=status.HTTP_400_BAD_REQUEST)
        if check_password(password, instructor_data['password']):
            (refresh, token) = GenerateTokens(instructor_data['id'], 'instructor')
            response = Response({
                "token": token,
                "user_data": instructor_data
            })
            response.set_cookie(
                key="token",
                value=refresh,
                httponly=True,
                samesite=None,
                secure=False,
                path='/'
            )
            return response
        return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)
class SignInStudentView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        # Start Check Data validation
        if username is None or password is None:
            return Response({
                "error": "smth wrong in inserted data",
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM student WHERE username = %s", (username,))
                student_temp_data = cursor.fetchall()
                if len(student_temp_data) == 0:
                    return Response({"error": "student not found",}, status=status.HTTP_404_NOT_FOUND)
                student_data = {
                    "id": student_temp_data[0][0],
                    "name": student_temp_data[0][1],
                    "email": student_temp_data[0][2],
                    "username": student_temp_data[0][3],
                    "password": student_temp_data[0][4],
                    "profilepic": student_temp_data[0][5],
                    "createdAt": student_temp_data[0][6],
                }
        except Exception as e:
            return Response({"error": str(e),}, status=status.HTTP_400_BAD_REQUEST)
        if check_password(password, student_data['password']):
            (refresh, token) = GenerateTokens(student_data['id'], 'student')
            response = Response({
                "token": token,
                "user_data": student_data
            })
            response.set_cookie(
                key="token",
                value=refresh,
                httponly=True,
                samesite=None,
                secure=False,
                path='/'
            )
            return response
        return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)    
class GenerateNewTokenView(APIView):
    authentication_classes = [CustomRefreshAuthentication]
    permission_classes = [AllowAny]
    def post(self, request):
        print(request.auth)
        (refresh, token) = GenerateTokens(request.user['id'], request.auth)
        response = Response({
            "token": token,
            "user_data": request.user
        })
        response.set_cookie(
            key="token",
            value=refresh,
            httponly=True,
            samesite=None,
            secure=False,
            path='/'
        )
        return response
class ResetPasswordView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def patch(self, request):
        new_password = request.data.get('new_password', None)
        if new_password is None:
            return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with connection.cursor() as cursor:
                print(request.user)
                temp_role = f"{request.auth}id"
                cursor.execute(f"UPDATE {request.auth} SET password = %s WHERE {temp_role} = %s", (make_password(new_password), request.user['id']))
                return Response({"message": "Password has been updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class LogoutView(APIView):
    authentication_classes = [CustomRefreshAuthentication]
    permission_classes = [AllowAny]
    def post(self, request):
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
class ForgetPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def put(self, request):
        email = request.data.get('email', None)
        role = request.data.get('role', None)
        if email is None or role is None:
            return Response({"error": "smth wring in passed data"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with connection.cursor() as cursor:
                if role == "instructor":
                    cursor.execute("SELECT instructorid FROM instructor WHERE email = %s", (email,))
                else:
                    cursor.execute("SELECT studentid FROM student WHERE email = %s", (email,))
                user = cursor.fetchall()
                if len(user) == 0:
                    return Response({"error": "user not found"}, status=status.HTTP_404_NOT_FOUND)
                (_, token) = GenerateTokens(user[0][0], role)
                reset_link = f"https://localhost:5173/?{token}"
                subject = "Forgot password"
                template = loader.get_template('email_template.html')
                html_message = template.render({'reset_link': reset_link})
                message = strip_tags(html_message)
                send_mail(
                    subject=subject,
                    message=message,
                    from_email="mbahgat503@gmail.com",
                    recipient_list=[email],
                    html_message=html_message
                )
                return Response({
                    "message": "Email has been sent to your email address",
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)