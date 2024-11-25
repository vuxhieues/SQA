from django.urls import path
from .views import *

urlpatterns = [
    path('create_course', CreateCourseView.as_view()),
    path('get_instructor_courses', GetInstructorCourses.as_view()),
    path('get_student_courses', GetStudentCourses.as_view()),
    path('enroll_student_to_course', StudentEnrollmentView.as_view()),
    path('ask_in_qa', AskInQAVideoView.as_view()),
    path('student_answers_in_qa', StudentAnswerInQAVideoView.as_view()),
    path('instructor_answers_in_qa', InstructorAnswerInQAVideoView.as_view()),
    path('instructor_add_quiz', AddQuiz.as_view()),
    path('add_instructor_to_course', AddInstructorToCourseView.as_view()),
    path('add_assignment', AddAssignment.as_view()),
    path('submit_assignment', SubmitAssignmentView.as_view()),
    path('grade_assignment', GradeAssignment.as_view()),
    path('get_single_course/<str:course_id>', GetSingleCourse.as_view()),
    path('get_quiz_exam/<str:quizID>', GetQuizExamView.as_view()),
]