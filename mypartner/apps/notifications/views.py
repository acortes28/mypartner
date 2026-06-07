from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notificacion
from .serializers import NotificacionSerializer


def _build_ref_context(notifications):
    """Bulk-fetch related objects to avoid N+1 queries in get_contexto_navegacion."""
    from apps.announcements.models import Anuncio
    from apps.finances.models import Movimiento, RegistroPresupuesto

    anuncio_ids, movimiento_ids, presupuesto_ids = [], [], []
    for n in notifications:
        if not n.referencia_id:
            continue
        if n.tipo == Notificacion.TIPO_ANUNCIO:
            anuncio_ids.append(n.referencia_id)
        elif n.tipo in (Notificacion.TIPO_GASTO, Notificacion.TIPO_INGRESO, Notificacion.TIPO_GASTO_COMPARTIDO):
            movimiento_ids.append(n.referencia_id)
        elif n.tipo == Notificacion.TIPO_PRESUPUESTO:
            presupuesto_ids.append(n.referencia_id)

    return {
        'anuncios': {
            str(a.id): a
            for a in Anuncio.objects.filter(id__in=anuncio_ids).only('id', 'grupo_id')
        } if anuncio_ids else {},
        'movimientos': {
            str(m.id): m
            for m in Movimiento.objects.filter(id__in=movimiento_ids).only('id', 'grupo_id')
        } if movimiento_ids else {},
        'presupuestos': {
            str(r.id): r
            for r in RegistroPresupuesto.objects.filter(id__in=presupuesto_ids).only('id', 'grupo_id')
        } if presupuesto_ids else {},
    }


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
        context = _build_ref_context(page)
        serializer = NotificacionSerializer(page, many=True, context=context)
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
