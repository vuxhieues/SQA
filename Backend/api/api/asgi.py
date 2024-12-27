"""
ASGI config for api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()
from django.urls import re_path
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter,URLRouter
from channels.auth import AuthMiddlewareStack
# from liveQA.routing import websocket_urlpatterns
from chat.routing import chat_websocket_urlpatterns
from django.conf import settings
from django.urls import path

# django.setup()

# from liveQA.consumer import *

# application = get_asgi_application()
print("DAAAAAAAAAMN")
application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(URLRouter(
        chat_websocket_urlpatterns
    ))
})