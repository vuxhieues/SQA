from rest_framework import permissions


class IsInstructor(permissions.BasePermission):
    """
    Custom permission to only allow instructors to access the view.
    """
    def has_permission(self, request, view):
        # Kiểm tra xem user có tồn tại và có role là instructor không
        if not request.user:
            return False
        return request.user.get('role') == 'instructor'

    def has_object_permission(self, request, view, obj):
        # Nếu cần kiểm tra permission cho object cụ thể
        return self.has_permission(request, view)

class IsStudent(permissions.BasePermission):
    """
    Custom permission to only allow students to access the view.
    """
    def has_permission(self, request, view):
        # Kiểm tra xem user có tồn tại và có role là student không
        if not request.user:
            return False
        return request.user.get('role') == 'student'

    def has_object_permission(self, request, view, obj):
        # Nếu cần kiểm tra permission cho object cụ thể
        return self.has_permission(request, view)
