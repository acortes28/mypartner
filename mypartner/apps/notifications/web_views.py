import json
import logging
import time

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import connection
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render, redirect

from .models import Notificacion

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 15  # segundos entre consultas


@login_required
def sse_notifications_view(request):
    user_id = request.user.id

    def event_stream():
        last_count = None
        tick = 0
        try:
            while True:
                try:
                    count = Notificacion.objects.filter(usuario_id=user_id, leida=False).count()
                    if count != last_count:
                        last_count = count
                        yield f"data: {json.dumps({'unread_count': count})}\n\n"
                    elif tick % 4 == 0:
                        yield ": heartbeat\n\n"
                except Exception:
                    logger.exception("SSE error para usuario %s", user_id)
                    return
                finally:
                    connection.close()
                tick += 1
                time.sleep(_POLL_INTERVAL)
        except GeneratorExit:
            pass

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
def notifications_unread_json_view(request):
    notifs = (
        Notificacion.objects
        .filter(usuario=request.user, leida=False)
        .order_by('-created_at')[:5]
    )
    return JsonResponse({
        'notifications': [
            {
                'id': str(n.id),
                'titulo': n.titulo,
                'tipo': n.tipo,
                'referencia_id': str(n.referencia_id) if n.referencia_id else None,
                'created_at': n.created_at.strftime('%d/%m/%Y %H:%M'),
            }
            for n in notifs
        ]
    })


@login_required
def notifications_view(request):
    qs = Notificacion.objects.filter(usuario=request.user).order_by('-created_at')
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'notifications/index.html', {'page': page})


@login_required
def mark_read_view(request, notification_id):
    try:
        notif = Notificacion.objects.get(id=notification_id, usuario=request.user)
        notif.leida = True
        notif.save()
    except Notificacion.DoesNotExist:
        return redirect('notifications-index')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})

    if notif.tipo == Notificacion.TIPO_INVITACION and notif.referencia_id:
        return redirect('invitation-detail', invitation_id=notif.referencia_id)
    if notif.tipo == Notificacion.TIPO_GASTO_COMPARTIDO:
        return redirect('finances-shared')
    if notif.tipo in (Notificacion.TIPO_GASTO, Notificacion.TIPO_INGRESO) and notif.referencia_id:
        return redirect('finances-movement-detail', movement_id=notif.referencia_id)
    if notif.tipo == Notificacion.TIPO_PRESUPUESTO:
        return redirect('finances-budget')
    if notif.tipo == Notificacion.TIPO_ANUNCIO and notif.referencia_id:
        from apps.announcements.models import Anuncio
        try:
            anuncio = Anuncio.objects.get(id=notif.referencia_id)
            return redirect('announcement-detail', group_id=anuncio.grupo_id, announcement_id=notif.referencia_id)
        except Anuncio.DoesNotExist:
            return redirect('notifications-index')

    return redirect('notifications-index')


@login_required
def mark_all_read_view(request):
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return redirect('notifications-index')
