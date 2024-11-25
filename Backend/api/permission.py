from rest_framework import permissions

class IsInstructor(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and their role is either 'user'
        return request.auth == 'instructor'

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and their role is 'admin'
        return request.auth == 'student'
