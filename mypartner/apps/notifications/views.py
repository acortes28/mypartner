from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notificacion
from .serializers import NotificacionSerializer


class NotificacionListView(APIView):
    def get(self, request):
        solo_no_leidas = request.query_params.get('unread') == 'true'
        qs = (
            Notificacion.objects
            .filter(usuario=request.user)
            .order_by('-created_at')
        )
        if solo_no_leidas:
            qs = qs.filter(leida=False)

        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(qs, request)
        serializer = NotificacionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MarkNotificacionReadView(APIView):
    def post(self, request, notification_id):
        updated = Notificacion.objects.filter(
            id=notification_id, usuario=request.user
        ).update(leida=True)
        if not updated:
            from rest_framework import status
            from rest_framework.response import Response
            return Response({'detail': 'Notificación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'detail': 'Notificación marcada como leída.'})


class MarkAllNotificacionesReadView(APIView):
    def post(self, request):
        Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
        return Response({'detail': 'Todas las notificaciones fueron marcadas como leídas.'})
