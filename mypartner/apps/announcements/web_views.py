from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from apps.groups.models import Grupo, GrupoMiembro
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from .models import Anuncio, Comentario


def _get_memberships(user):
    return (
        GrupoMiembro.objects
        .filter(usuario=user, grupo__activo=True)
        .select_related('grupo')
        .order_by('grupo__nombre')
    )


@login_required
def announcements_select_view(request):
    """Selector de grupo. Si el usuario solo tiene uno, redirige directamente."""
    memberships = _get_memberships(request.user)
    if not memberships.exists():
        messages.info(request, 'Para acceder a Anuncios necesitas pertenecer a un grupo.')
        return redirect('group-manage')
    if memberships.count() == 1:
        return redirect('announcements-group', group_id=memberships.first().grupo_id)
    return render(request, 'announcements/group_select.html', {'memberships': memberships})


@login_required
def announcements_view(request, group_id):
    grupo = get_object_or_404(Grupo, id=group_id, activo=True)
    if not GrupoMiembro.objects.filter(usuario=request.user, grupo=grupo).exists():
        messages.error(request, 'No perteneces a este grupo.')
        return redirect('announcements-index')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        if not nombre or not descripcion:
            messages.error(request, 'Nombre y descripción son obligatorios.')
        else:
            anuncio = Anuncio.objects.create(
                nombre=nombre, descripcion=descripcion,
                usuario=request.user, grupo=grupo,
            )
            crear_notificaciones_grupo(
                grupo, Notificacion.TIPO_ANUNCIO,
                f'Se realizó el siguiente anuncio: {nombre}',
                referencia_id=anuncio.id, excluir_usuario=request.user,
            )
            messages.success(request, 'Anuncio publicado.')
        return redirect('announcements-group', group_id=group_id)

    anuncios = (
        Anuncio.objects.filter(grupo=grupo, activo=True)
        .select_related('usuario').order_by('-created_at')
    )
    return render(request, 'announcements/index.html', {
        'grupo': grupo,
        'anuncios': anuncios,
        'multi_grupo': _get_memberships(request.user).count() > 1,
    })


@login_required
def announcement_detail_view(request, group_id, announcement_id):
    grupo = get_object_or_404(Grupo, id=group_id, activo=True)
    if not GrupoMiembro.objects.filter(usuario=request.user, grupo=grupo).exists():
        messages.error(request, 'No perteneces a este grupo.')
        return redirect('announcements-index')

    anuncio = get_object_or_404(Anuncio, id=announcement_id, grupo=grupo, activo=True)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'comment':
            contenido = request.POST.get('contenido', '').strip()
            if contenido:
                Comentario.objects.create(contenido=contenido, anuncio=anuncio, usuario=request.user)
                messages.success(request, 'Comentario agregado.')
            else:
                messages.error(request, 'El comentario no puede estar vacío.')
        elif action == 'delete' and anuncio.usuario == request.user:
            anuncio.activo = False
            anuncio.save()
            messages.success(request, 'Anuncio eliminado.')
            return redirect('announcements-group', group_id=group_id)
        return redirect('announcement-detail', group_id=group_id, announcement_id=announcement_id)

    comentarios = anuncio.comentarios.select_related('usuario').order_by('created_at')
    return render(request, 'announcements/detail.html', {
        'grupo': grupo,
        'anuncio': anuncio,
        'comentarios': comentarios,
    })
