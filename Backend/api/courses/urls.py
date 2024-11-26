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
    path('instructor_add_quiz', AddQuizView.as_view()),
    path('add_instructor_to_course', AddInstructorToCourseView.as_view()),
    path('add_assignment', AddAssignment.as_view()),
    path('submit_assignment', SubmitAssignmentView.as_view()),
    path('grade_assignment', GradeAssignment.as_view()),
    path('get_single_course/<str:course_id>', GetSingleCourse.as_view()),
    path('get_quiz_exam/<str:quizID>', GetQuizExamView.as_view()),

    path("update_quiz", UpdateQuizView.as_view()),
    path("update_assignment/<str:assignmentId>", UpdateAssignment.as_view()),
    path("update_video", UpdateVideo.as_view()),
    path("update_section", UpdateSectionView.as_view()),

    path("add_video", AddVideo.as_view()),
    path("add_section", AddSectionsView.as_view()),

    path("make_contest", MakeContest.as_view()),
    path("delete_contest/<str:contestId>", DeleteContest.as_view()),

    path("get_categories", GetCategories.as_view()),
    path("search_by_title", SearchByTtitle.as_view()),
    path("search_by_categories", SearchByCategories.as_view()),

    path("delete_course/<str:courseId>", DeleteCourseView.as_view()),
    path("delete_section/<str:sectionId>", DeleteSectionView.as_view()),
    path("delete_video/<str:videoId>", DeleteVideoView.as_view()),
    path("delete_assignment/<str:assignmentId>", DeleteAssignmentView.as_view()),
    path("delete_quiz/<str:quizId>", DeleteQuizView.as_view()),
]