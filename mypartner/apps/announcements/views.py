from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.groups.models import Grupo
from apps.groups.permissions import IsGroupMember
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from .models import Anuncio, Comentario
from .serializers import (
    AnuncioCreateSerializer,
    AnuncioDetailSerializer,
    AnuncioListSerializer,
    ComentarioCreateSerializer,
    ComentarioSerializer,
)


class AnuncioListCreateView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id):
        anuncios = (
            Anuncio.objects
            .filter(grupo_id=group_id, activo=True)
            .select_related('usuario')
            .order_by('-created_at')
        )
        serializer = AnuncioListSerializer(anuncios, many=True)
        return Response(serializer.data)

    def post(self, request, group_id):
        try:
            grupo = Grupo.objects.get(id=group_id, activo=True)
        except Grupo.DoesNotExist:
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AnuncioCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        anuncio = serializer.save(usuario=request.user, grupo=grupo)

        crear_notificaciones_grupo(
            grupo,
            Notificacion.TIPO_ANUNCIO,
            f'Se realizó el siguiente anuncio: {anuncio.nombre}',
            referencia_id=anuncio.id,
            excluir_usuario=request.user,
        )

        return Response(AnuncioListSerializer(anuncio).data, status=status.HTTP_201_CREATED)


class AnuncioDetailDeleteView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id, announcement_id):
        try:
            anuncio = (
                Anuncio.objects
                .prefetch_related('comentarios__usuario')
                .select_related('usuario')
                .get(id=announcement_id, grupo_id=group_id, activo=True)
            )
        except Anuncio.DoesNotExist:
            return Response({'detail': 'Anuncio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AnuncioDetailSerializer(anuncio)
        return Response(serializer.data)

    def delete(self, request, group_id, announcement_id):
        try:
            anuncio = Anuncio.objects.get(
                id=announcement_id, grupo_id=group_id, activo=True
            )
        except Anuncio.DoesNotExist:
            return Response({'detail': 'Anuncio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if anuncio.usuario != request.user:
            return Response(
                {'detail': 'Solo el autor puede eliminar el anuncio.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        anuncio.activo = False
        anuncio.save()
        return Response({'detail': 'Anuncio eliminado.'})


class ComentarioCreateView(APIView):
    permission_classes = [IsGroupMember]

    def post(self, request, group_id, announcement_id):
        try:
            anuncio = Anuncio.objects.get(
                id=announcement_id, grupo_id=group_id, activo=True
            )
        except Anuncio.DoesNotExist:
            return Response({'detail': 'Anuncio no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ComentarioCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comentario = serializer.save(usuario=request.user, anuncio=anuncio)
        return Response(ComentarioSerializer(comentario).data, status=status.HTTP_201_CREATED)
