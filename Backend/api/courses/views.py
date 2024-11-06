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
from permission import IsInstructor, IsStudent
# Create your views here.

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
        course_image = request.FILES.get('course_image', "")
        certificate = request.FILES.get('certificate', "")
        sections = request.data.get('sections', None)
        if title is None or description is None or categoryID is None or seen_status is None or price is None or sections is None:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        query = """
            INSERT INTO course (title, description, categoryid, seenstatus, price, requirements)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING courseID;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (title, description, categoryID, seen_status, price, requirements))
                course_id = cursor.fetchone()[0]
        except Exception as e:
            return Response({"errors": str(e),}, status=status.HTTP_400_BAD_REQUEST)
        print("course_image: ", course_image)
        if course_image is not None:
            try:
                upload_result = cloudinary.uploader.upload(course_image)
                image_url = upload_result['secure_url']
                query = """
                    UPDATE course
                    SET courseimage = %s
                    WHERE courseid = %s;
                """ 
                print(image_url, course_id)
                with connection.cursor() as cursor:
                    cursor.execute(query, (image_url, course_id))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if certificate is not None:
            try:
                upload_result = cloudinary.uploader.upload(certificate)
                image_url = upload_result['secure_url']
                query = """
                    UPDATE course
                    SET certificate = %s
                    WHERE courseid = %s;
                """
                print(image_url, course_id)
                with connection.cursor() as cursor:
                    cursor.execute(query, (image_url, course_id))
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        for section_index, section in sections:
            section_title = section["title"]
            section_videos = section["videos"]
            create_section_query = """
                INSERT INTO coursesection (courseid, title)
                VALUES (%s, %s);
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute(create_section_query, (course_id, section_title))
                    section_id = cursor.fetchone()[0]
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            for video_index, video in enumerate(section_videos):
                video_title = video["title"]
                video = request.FILES.get(f'video_{section_index}_{video_index}', None)
                if video is not None:
                    try:
                        upload_result = cloudinary.uploader.upload(video)
                        video_url = upload_result['secure_url']
                        craete_video_query = """
                            INSERT INTO video (coursesectionid, title, videolink)
                            VALUES (%s, %s, %s)
                        """ 
                        print(image_url, course_id)
                        with connection.cursor() as cursor:
                            cursor.execute(craete_video_query, (section_id, video_title, video_url))
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        "error": f"Video {video_index} in section {section_index} is missing"
                        }, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Instructor created successfully"}, status=status.HTTP_201_CREATED)
class GetInstructorCourses(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsInstructor]
    def get(self, request):
        top_instructor_courses = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM course WHERE topinstructorid = %s", (request.user['id'],))
                top_instructor_courses = cursor.fetchall()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        non_top_instructor_courses = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT courseid FROM course_instructor WHERE instructorid = %s", (request.user['id'],))
                non_top_instructor_courses = cursor.fetchall()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "top_instructor_courses": top_instructor_courses,
            "non_top_instructor_courses": non_top_instructor_courses
        }, status=status.HTTP_200_OK)
class GetStudentCourses(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def get(self, request):
        courses = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM student_course AS sc INNER JOIN course AS c ON sc.courseid = c.courseid and sc.studentid = %s;", (request.user['id'],))
                courses = cursor.fetchall()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"courses": courses}, status=status.HTTP_200_OK)
class GetSingleCourse(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsStudent]
    def get(self, request, course_id):
        course_id = int(course_id)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM course WHERE courseid = %s", (course_id,))
                temp_data = cursor.fetchall()
                data = {
                    "id": temp_data[0][0],
                    "title": temp_data[0][1],
                    "description": temp_data[0][2],
                    "top_instructor_id": temp_data[0][3],
                    "categoryId": temp_data[0][4],
                    "seen_status": temp_data[0][5],
                    "duration": temp_data[0][6],
                    "createdAt": temp_data[0][7],
                    "price": temp_data[0][8],
                    "rating": temp_data[0][9],
                    "requirements": temp_data[0][10],
                    "CourseImage": temp_data[0][11],
                    "Certificate": temp_data[0][13]
                }
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "course": data
        }, status=status.HTTP_200_OK)

