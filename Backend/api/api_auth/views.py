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
# Create your views here.

class SignUpAsInstructorView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        name = request.data.get("name", None)
        email = request.data.get("email", None)
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        Bio = request.data.get("Bio", "")
        SocialMedia = request.data.get("SocialMedia", "")
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
                    UPDATE instructor
                    SET profilepic = %s
                    WHERE instructorid = %s;
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