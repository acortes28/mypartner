from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from .models import Grupo, GrupoMiembro, Invitacion
from .permissions import IsGroupAdmin, IsGroupMember
from .serializers import (
    CreateGrupoSerializer,
    GrupoSerializer,
    InvitacionSerializer,
    InvitarUsuarioSerializer,
    RemoverMiembroSerializer,
    SetRolSerializer,
)


def _get_user_group(user):
    membership = (
        GrupoMiembro.objects
        .filter(usuario=user, grupo__activo=True)
        .select_related('grupo')
        .first()
    )
    return membership


class MyGroupView(APIView):
    def get(self, request):
        membership = _get_user_group(request.user)
        if not membership:
            return Response({'grupo': None, 'mensaje': 'Sin grupo'})
        serializer = GrupoSerializer(membership.grupo)
        return Response({'grupo': serializer.data, 'rol': membership.rol})


class CreateGroupView(APIView):
    def post(self, request):
        if _get_user_group(request.user):
            return Response(
                {'detail': 'Ya perteneces a un grupo. Abandónalo antes de crear uno nuevo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CreateGrupoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grupo = serializer.save()
        GrupoMiembro.objects.create(usuario=request.user, grupo=grupo, rol=GrupoMiembro.ROL_ADMIN)
        return Response(GrupoSerializer(grupo).data, status=status.HTTP_201_CREATED)


class DeleteGroupView(APIView):
    permission_classes = [IsGroupAdmin]

    def delete(self, request, group_id):
        try:
            grupo = Grupo.objects.get(id=group_id, activo=True)
        except Grupo.DoesNotExist:
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        grupo.activo = False
        grupo.save()
        return Response({'detail': f'El grupo "{grupo.nombre}" fue eliminado.'})


class InviteMemberView(APIView):
    permission_classes = [IsGroupAdmin]

    def post(self, request, group_id):
        try:
            grupo = Grupo.objects.get(id=group_id, activo=True)
        except Grupo.DoesNotExist:
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = InvitarUsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receptor = serializer.validated_data['username']
        comentario = serializer.validated_data.get('comentario', '')

        if GrupoMiembro.objects.filter(usuario=receptor, grupo=grupo).exists():
            return Response(
                {'detail': 'Este usuario ya es miembro del grupo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar bloqueo por rechazos repetidos
        una_hora_atras = timezone.now() - timedelta(hours=1)
        rechazos_recientes = Invitacion.objects.filter(
            emisor=request.user,
            receptor=receptor,
            estado=Invitacion.ESTADO_RECHAZADA,
            updated_at__gte=una_hora_atras,
        ).count()
        if rechazos_recientes >= 2:
            return Response(
                {'detail': 'No puedes enviar invitaciones a este usuario por las próximas 24 horas.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        invitacion = Invitacion.objects.create(
            emisor=request.user,
            receptor=receptor,
            grupo=grupo,
            comentario=comentario,
        )

        Notificacion.objects.create(
            titulo=f'El usuario {request.user.username} te ha invitado al grupo {grupo.nombre}',
            tipo=Notificacion.TIPO_INVITACION,
            referencia_id=invitacion.id,
            usuario=receptor,
        )

        return Response({'detail': 'Invitación enviada exitosamente.'}, status=status.HTTP_201_CREATED)


class RemoveMemberView(APIView):
    permission_classes = [IsGroupAdmin]

    def post(self, request, group_id):
        serializer = RemoverMiembroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario_id = serializer.validated_data['usuario_id']

        if str(request.user.id) == str(usuario_id):
            return Response(
                {'detail': 'No puedes expulsarte a ti mismo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            membership = GrupoMiembro.objects.get(usuario_id=usuario_id, grupo_id=group_id)
        except GrupoMiembro.DoesNotExist:
            return Response({'detail': 'Miembro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        username = membership.usuario.username
        membership.delete()
        return Response({'detail': f'El usuario {username} fue expulsado del grupo.'})


class SetRoleView(APIView):
    permission_classes = [IsGroupAdmin]

    def post(self, request, group_id):
        serializer = SetRolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario_id = serializer.validated_data['usuario_id']
        nuevo_rol = serializer.validated_data['rol']

        if str(request.user.id) == str(usuario_id):
            return Response(
                {'detail': 'No puedes cambiar tu propio rol.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            membership = GrupoMiembro.objects.get(usuario_id=usuario_id, grupo_id=group_id)
        except GrupoMiembro.DoesNotExist:
            return Response({'detail': 'Miembro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        membership.rol = nuevo_rol
        membership.save()
        action = 'ahora es administrador' if nuevo_rol == GrupoMiembro.ROL_ADMIN else 'ya no es administrador'
        return Response({'detail': f'El usuario {membership.usuario.username} {action}.'})


class LeaveGroupView(APIView):
    def post(self, request, group_id):
        try:
            membership = GrupoMiembro.objects.get(
                usuario=request.user,
                grupo_id=group_id,
                grupo__activo=True,
            )
        except GrupoMiembro.DoesNotExist:
            return Response({'detail': 'No perteneces a este grupo.'}, status=status.HTTP_404_NOT_FOUND)

        if membership.rol == GrupoMiembro.ROL_ADMIN:
            other_admins = GrupoMiembro.objects.filter(
                grupo_id=group_id, rol=GrupoMiembro.ROL_ADMIN
            ).exclude(usuario=request.user)
            if not other_admins.exists():
                return Response(
                    {'detail': 'Debes asignar otro administrador antes de abandonar el grupo.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        membership.delete()
        return Response({'detail': 'Abandonaste el grupo exitosamente.'})


class InvitationListView(APIView):
    def get(self, request):
        invitaciones = Invitacion.objects.filter(
            receptor=request.user,
            estado=Invitacion.ESTADO_PENDIENTE,
        ).select_related('grupo', 'emisor').order_by('-created_at')
        serializer = InvitacionSerializer(invitaciones, many=True)
        return Response(serializer.data)


class AcceptInvitationView(APIView):
    def post(self, request, invitation_id):
        try:
            invitacion = Invitacion.objects.select_related('grupo', 'emisor').get(
                id=invitation_id,
                receptor=request.user,
                estado=Invitacion.ESTADO_PENDIENTE,
            )
        except Invitacion.DoesNotExist:
            return Response({'detail': 'Invitación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if not invitacion.grupo.activo:
            return Response({'detail': 'El grupo ya no existe.'}, status=status.HTTP_400_BAD_REQUEST)

        # Salir del grupo actual si tiene uno
        GrupoMiembro.objects.filter(usuario=request.user).delete()

        GrupoMiembro.objects.create(
            usuario=request.user,
            grupo=invitacion.grupo,
            rol=GrupoMiembro.ROL_MIEMBRO,
        )
        invitacion.estado = Invitacion.ESTADO_ACEPTADA
        invitacion.save()

        return Response({'detail': f'Te uniste al grupo {invitacion.grupo.nombre} exitosamente.'})


class RejectInvitationView(APIView):
    def post(self, request, invitation_id):
        try:
            invitacion = Invitacion.objects.select_related('grupo', 'emisor').get(
                id=invitation_id,
                receptor=request.user,
                estado=Invitacion.ESTADO_PENDIENTE,
            )
        except Invitacion.DoesNotExist:
            return Response({'detail': 'Invitación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        invitacion.estado = Invitacion.ESTADO_RECHAZADA
        invitacion.save()

        return Response({'detail': 'Invitación rechazada.'})
