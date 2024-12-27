from django.urls import path
from .views import *

urlpatterns = [
    path("get_chat_rooms/<str:course_id>", GetCourseChatRooms.as_view()),
]