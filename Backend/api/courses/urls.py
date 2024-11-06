from django.urls import path
from .views import *

urlpatterns = [
    path('create_course', CreateCourseView.as_view()),
    path('get_instructor_courses', GetInstructorCourses.as_view()),
    path('get_single_course/<str:course_id>', GetStudentCourses.as_view()),
]