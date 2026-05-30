from rest_framework.permissions import BasePermission
from .models import GrupoMiembro


class IsGroupMember(BasePermission):
    """Valida que el usuario autenticado pertenece al grupo indicado en la URL."""

    def has_permission(self, request, view):
        group_id = view.kwargs.get('group_id')
        if not group_id:
            return False
        return GrupoMiembro.objects.filter(
            usuario=request.user, grupo_id=group_id
        ).exists()


class IsGroupAdmin(BasePermission):
    """Valida que el usuario autenticado tiene rol admin en el grupo indicado en la URL."""

    def has_permission(self, request, view):
        group_id = view.kwargs.get('group_id')
        if not group_id:
            return False
        return GrupoMiembro.objects.filter(
            usuario=request.user,
            grupo_id=group_id,
            rol=GrupoMiembro.ROL_ADMIN,
        ).exists()


class IsOwnerOrReadOnly(BasePermission):
    """Permite escritura solo al dueño del objeto (campo `usuario`)."""

    def has_object_permission(self, request, view, obj):
        return obj.usuario == request.user
