from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework.exceptions import AuthenticationFailed
from authenticate import CustomRefreshAuthentication, CustomTokenAuthentication
from django.db import connection
from asgiref.sync import sync_to_async
import json
import asyncio
import contextlib

class Request:
    def __init__(self, headers):
        self.headers = headers

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract the room name and token from the URL
        self.chat_id = self.scope['url_route']['kwargs'].get('chat_id', None)
        token = self.scope['query_string'].decode().split('token=')[1] if 'token=' in self.scope['query_string'].decode() else None

        if not token:
            await self.close()
            return

        # Authenticate user
        try:
            auth_result = await sync_to_async(self.authenticate_user)(token)
            self.user, self.role = auth_result
        except Exception as e:
            print(f"Authentication error: {e}")
            await self.close()
            return

        if not self.user:
            await self.close()
            return

        # Join the chat group
        await self.channel_layer.group_add(
            f'{self.chat_id}',
            self.channel_name
        )

        await self.accept()
        await self.send_all_previous_messages()

        print("WebSocket connected")

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        
        # Send message to group
        await self.channel_layer.group_send(
            f"{self.chat_id}",
            {
                'type': 'chat_message',
                'sender': self.user,
                'role': self.role,
                'message': message
            }
        )

        # Create task for saving message
        asyncio.create_task(self.save_message_async(message, self.user, self.role))

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        role = event['role']
        
        sender_info = {
            'id': sender.get('id'),
            'name': sender.get('name'),
            'username': sender.get('username'),
            'role': role,
            'profilepic': sender.get('profilepic')
        }
        
        await self.send(text_data=json.dumps({
            'sender': sender_info,
            'message': message
        }))

    async def save_message_async(self, message, sender, role):
        """Async wrapper for saving messages"""
        await sync_to_async(self._save_message)(message, sender, role)

    def _save_message(self, message, sender, role):
        """Synchronous message saving function"""
        print(message)
        print(sender)
        print(role)
        print(self.chat_id)
        
        query = """
            INSERT INTO Messages (MessageText, isAnswer, AnswerTo, SenderStudentID, SenderInstructorID, QAID, ChatID)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        
        sender_student_id = sender["id"] if role == "student" else None
        sender_instructor_id = sender["id"] if role == "instructor" else None

        with contextlib.closing(connection.cursor()) as cursor:
            try:
                cursor.execute(
                    query,
                    (message, False, None, sender_student_id, sender_instructor_id, None, self.chat_id)
                )
            except Exception as e:
                print(f"Database error: {e}")
                connection.rollback()
                raise

    async def send_all_previous_messages(self):
        """Fetch all previous messages for the chat and send them to the client."""
        messages = await sync_to_async(self._fetch_previous_messages)()
        
        if len(messages) == 0:
            await self.send(text_data=json.dumps({
                'sender': {
                    'id': None,
                    'role': None,
                },
                'message': None
            }))
        for message in messages:
            await self.send(text_data=json.dumps({
                'sender': {
                    'id': message.get('SenderID'),
                    'role': message.get('SenderRole'),
                },
                'message': message.get('MessageText')
            }))

    def _fetch_previous_messages(self):
        """Synchronous method to fetch previous messages from the database."""
        query = """
            SELECT * FROM Messages WHERE ChatID = %s ORDER BY MessageID ASC
        """
        with contextlib.closing(connection.cursor()) as cursor:
            try:
                cursor.execute(query, (self.chat_id,))
                messages = [
                    {
                        'MessageText': row[1],
                        'SenderID': row[4] or row[5], # Either StudentID or InstructorID
                        'SenderRole': 'student' if row[4] else 'instructor'
                    }
                    for row in cursor.fetchall()
                ]
                print(messages)
                return messages
            except Exception as e:
                print(f"Database error while fetching messages: {e}")
                return []

    def authenticate_user(self, token):
        """Async wrapper for user authentication"""
        request = Request(headers={'token': token})
        authentication_class = CustomTokenAuthentication()
        return authentication_class.authenticate(request)

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'chat_id'):  # Fixed reference to self.room
            await self.channel_layer.group_discard(
                f"{self.chat_id}",  # Fixed reference to self.courseId
                self.channel_name
            )
        print("WebSocket disconnected with code:", close_code)

class LiveQAConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract the room name from the URL
        course_id = self.scope['url_route']['kwargs'].get('course_id', None)
        # Extract the token from the URL
        token = self.scope['query_string'].decode().split('token=')[1] if 'token=' in self.scope['query_string'].decode() else None
        
        if not token:
            await self.close()
            return

        self.user = await (sync_to_async)(self.authenticate_user)(token)
        if not self.user:
            await self.close()
            return
        
        self.courseId = course_id

        # try:
        #     self.room = Room.objects.get(id=room_id)
        # except DoesNotExist:
        #     await self.close()
        #     return

        # Join room group
        await self.channel_layer.group_add(
            f'{self.courseId}',
            self.channel_name
        )
        await self.accept()
        print("WebSocket connected")

    async def receive(self, text_data=None, bytes_data=None):
        # Handle incoming data
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        await self.channel_layer.group_send(
            f"{self.courseId}",
            {
                'type': 'chat_message',
                'sender': self.user,
                'message': message
            }
        )

    async def chat_message(self, event):
        # Send the message to WebSocket
        message = event['message']
        sender = event['sender']
        sender_info = {
            'id': sender.get('id'),
            'name': sender.get('name'),
            'username': sender.get('username'),
            'profilepic': sender.get('profilepic')
        }
        await self.send(text_data=json.dumps({
            'sender': sender_info,
            'message': message
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        if self.courseId:
            await self.channel_layer.group_discard(
                f"{self.courseId}",
                self.channel_name
            )
        print("WebSocket disconnected with code:", close_code)

    def authenticate_user(self, token):
        # Authenticate user with token
        request = Request(headers={
            'token': token
        })
        authentication_class = CustomTokenAuthentication()
        (user, _) = authentication_class.authenticate(request)
        return user