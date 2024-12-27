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
from courses.views import get_instructor_raw_data, get_student_raw_data

# Create your views here.

class GetCourseChatRooms(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [AllowAny]
    def get(self, request, course_id):
        if request.auth == "instructor":
            with connection.cursor() as cursor:
                print(course_id, request.user["id"])
                cursor.execute("SELECT * FROM Chat WHERE CourseID = %s AND InstructorID = %s", (course_id,request.user["id"]))
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in rows]
                for i, datum in enumerate(data):
                    student_data = get_student_raw_data(datum["studentid"])
                    data[i]["student"] = student_data
                    del data[i]["studentid"]
                return Response(data, status=status.HTTP_200_OK)
        elif request.auth == "student":
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Chat WHERE CourseID = %s AND StudentID = %s", (course_id,request.user["id"]))
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in rows]
                for i, datum in enumerate(data):
                    instructor_data = get_instructor_raw_data(datum["instructorid"])
                    data[i]["instructor"] = instructor_data
                    del data[i]["instructorid"]
                return Response(data, status=status.HTTP_200_OK)
