from django.urls import re_path
from .consumer import *

print("CHAT")
chat_websocket_urlpatterns = [
    re_path(r'^ws/chat/private_chat/(?P<chat_id>\w+)', ChatConsumer.as_asgi()),
    re_path(r'ws/chat/connect_to_liveqa_room/(?P<course_id>\w+)', LiveQAConsumer.as_asgi()),
]