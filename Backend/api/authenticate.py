from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.db import connection

def GenerateTokens(id, role):
    # Generate tokens for the given text
    refresh_token = RefreshToken()
    refresh_token["id"] = id
    refresh_token["role"] = role
    return (str(refresh_token), str(refresh_token.access_token))

class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get("token", None)
        if token is None:
            raise AuthenticationFailed("token is not provided")
        try:
            validated_token = AccessToken(token)
            user_id = validated_token["id"]
            role = validated_token["role"]
        except InvalidToken as e:
            raise AuthenticationFailed("Invalid token")
        except TokenError as e:
            raise AuthenticationFailed("expired token or another error")
        with connection.cursor() as cursor:
            temp_string = f"{role}id"
            cursor.execute(f"SELECT * FROM {role} WHERE {temp_string} = %s;", (user_id,))
            temp_user_data = cursor.fetchall()
            user_data = {}
            if role == 'instructor':
                user_data = {
                    "id": temp_user_data[0][0],
                    "name": temp_user_data[0][1],
                    "email": temp_user_data[0][2],
                    "username": temp_user_data[0][3],
                    "password": temp_user_data[0][4],
                    "profilepic": temp_user_data[0][5],
                    "bio": temp_user_data[0][6],
                    "rating": temp_user_data[0][7],
                    "createdAt": temp_user_data[0][8],
                    "social_media": temp_user_data[0][9],
                }
            else:
                user_data = {
                    "id": temp_user_data[0][0],
                    "name": temp_user_data[0][1],
                    "email": temp_user_data[0][2],
                    "username": temp_user_data[0][3],
                    "password": temp_user_data[0][4],
                    "profilepic": temp_user_data[0][5],
                    "createdAt": temp_user_data[0][6],
                }
            return (user_data, role)
        
class CustomRefreshAuthentication(BaseAuthentication):
    def authenticate(self, request):
        refresh = request.headers.get("refresh", None)
        if refresh is None:
            raise AuthenticationFailed("refresh token is not provided")
        try:
            validated_refresh = RefreshToken(refresh)
            user_id = validated_refresh["id"]
            role = validated_refresh["role"]
            validated_refresh.blacklist()
        except InvalidToken:
            raise AuthenticationFailed("refresh token is invalid")
        except TokenError as e:
            raise AuthenticationFailed("refresh token is expired")
        with connection.cursor() as cursor:
            temp_string = f"{role}id"
            cursor.execute(f"SELECT * FROM {role} WHERE {temp_string} = %s;", (user_id,))
            temp_user_data = cursor.fetchall()
            user_data = {}
            if role == 'instructor':
                user_data = {
                    "id": temp_user_data[0][0],
                    "name": temp_user_data[0][1],
                    "email": temp_user_data[0][2],
                    "username": temp_user_data[0][3],
                    "password": temp_user_data[0][4],
                    "profilepic": temp_user_data[0][5],
                    "bio": temp_user_data[0][6],
                    "rating": temp_user_data[0][7],
                    "createdAt": temp_user_data[0][8],
                    "social_media": temp_user_data[0][9],
                }
            else:
                user_data = {
                    "id": temp_user_data[0][0],
                    "name": temp_user_data[0][1],
                    "email": temp_user_data[0][2],
                    "username": temp_user_data[0][3],
                    "password": temp_user_data[0][4],
                    "profilepic": temp_user_data[0][5],
                    "createdAt": temp_user_data[0][6],
                }
            return (user_data, role)