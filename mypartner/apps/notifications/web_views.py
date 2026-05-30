from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .models import Notificacion


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
    if notif.tipo in (Notificacion.TIPO_GASTO, Notificacion.TIPO_INGRESO) and notif.referencia_id:
        return redirect('finances-movement-detail', movement_id=notif.referencia_id)
    if notif.tipo == Notificacion.TIPO_PRESUPUESTO:
        return redirect('finances-budget')
    if notif.tipo == Notificacion.TIPO_ANUNCIO and notif.referencia_id:
        return redirect('announcement-detail', announcement_id=notif.referencia_id)

    return redirect('notifications-index')


@login_required
def mark_all_read_view(request):
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return redirect('notifications-index')
