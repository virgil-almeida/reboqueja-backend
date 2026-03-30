from rest_framework import permissions

from .models import UserRole


class IsMotorista(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and getattr(u, 'role', None) == UserRole.MOTORISTA
            and hasattr(u, 'motorista')
        )


class IsPrestador(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and getattr(u, 'role', None) == UserRole.PRESTADOR
            and hasattr(u, 'prestador')
        )
