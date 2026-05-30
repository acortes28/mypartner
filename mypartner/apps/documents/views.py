import os

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.groups.models import Grupo
from apps.groups.permissions import IsGroupMember
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from .models import Documento
from .serializers import DocumentoCreateSerializer, DocumentoSerializer


class DocumentoListCreateView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id):
        documentos = (
            Documento.objects
            .filter(grupo_id=group_id, activo=True)
            .select_related('usuario')
            .order_by('-created_at')
        )
        serializer = DocumentoSerializer(documentos, many=True)
        return Response(serializer.data)

    def post(self, request, group_id):
        try:
            grupo = Grupo.objects.get(id=group_id, activo=True)
        except Grupo.DoesNotExist:
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DocumentoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archivo = serializer.validated_data['archivo']
        ext = os.path.splitext(archivo.name)[1].lstrip('.').lower()

        documento = serializer.save(
            usuario=request.user,
            grupo=grupo,
            tipo_archivo=ext,
            tamano_bytes=archivo.size,
        )

        crear_notificaciones_grupo(
            grupo,
            Notificacion.TIPO_ANUNCIO,
            f'{request.user.username} subió el documento "{documento.nombre}"',
            referencia_id=documento.id,
            excluir_usuario=request.user,
        )

        return Response(DocumentoSerializer(documento).data, status=status.HTTP_201_CREATED)


class DocumentoDeleteView(APIView):
    permission_classes = [IsGroupMember]

    def delete(self, request, group_id, document_id):
        try:
            documento = Documento.objects.get(id=document_id, grupo_id=group_id, activo=True)
        except Documento.DoesNotExist:
            return Response({'detail': 'Documento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if documento.usuario != request.user:
            return Response(
                {'detail': 'Solo el usuario que subió el documento puede eliminarlo.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        documento.activo = False
        documento.save()
        return Response({'detail': 'Documento eliminado.'})
