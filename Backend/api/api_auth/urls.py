from django.urls import path
from .views import *

urlpatterns = [
    path("instrutor_sign_up", SignUpAsInstructorView.as_view()),
    path("instrutor_sign_in", SignInInstructorView.as_view()),
    path("student_sign_up", SignUpAsStudentView.as_view()),
    path("student_sign_in", SignInStudentView.as_view()),
    path("generate_new_token", GenerateNewTokenView.as_view()),
    path("reset_password", ResetPasswordView.as_view()),
    path("forgot_password", ForgetPasswordView.as_view()),
    path("logout", LogoutView.as_view()),
    path("get_student_data/<str:student_id>", GetStudentData.as_view()),
    path("new_db", ChangeDB.as_view()),
]