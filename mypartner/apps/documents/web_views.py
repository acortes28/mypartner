import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from apps.groups.models import Grupo, GrupoMiembro
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from .models import Documento, ALLOWED_EXTENSIONS


def _get_memberships(user):
    return (
        GrupoMiembro.objects
        .filter(usuario=user, grupo__activo=True)
        .select_related('grupo')
        .order_by('grupo__nombre')
    )


@login_required
def documents_select_view(request):
    """Selector de grupo. Si el usuario solo tiene uno, redirige directamente."""
    memberships = _get_memberships(request.user)
    if not memberships.exists():
        messages.info(request, 'Para acceder a Documentos necesitas pertenecer a un grupo.')
        return redirect('group-manage')
    if memberships.count() == 1:
        return redirect('documents-group', group_id=memberships.first().grupo_id)
    return render(request, 'documents/group_select.html', {'memberships': memberships})


@login_required
def documents_view(request, group_id):
    grupo = get_object_or_404(Grupo, id=group_id, activo=True)
    if not GrupoMiembro.objects.filter(usuario=request.user, grupo=grupo).exists():
        messages.error(request, 'No perteneces a este grupo.')
        return redirect('documents-index')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'upload':
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            archivo = request.FILES.get('archivo')
            if not archivo or not nombre:
                messages.error(request, 'Nombre y archivo son obligatorios.')
            else:
                ext = os.path.splitext(archivo.name)[1].lstrip('.').lower()
                if ext not in ALLOWED_EXTENSIONS:
                    messages.error(request, f'Formato no permitido. Solo: {", ".join(ALLOWED_EXTENSIONS)}.')
                elif archivo.size > 10 * 1024 * 1024:
                    messages.error(request, 'El archivo no puede superar los 10 MB.')
                else:
                    doc = Documento.objects.create(
                        nombre=nombre, descripcion=descripcion, archivo=archivo,
                        tipo_archivo=ext, tamano_bytes=archivo.size,
                        usuario=request.user, grupo=grupo,
                    )
                    crear_notificaciones_grupo(
                        grupo, Notificacion.TIPO_ANUNCIO,
                        f'{request.user.username} subió el documento "{nombre}"',
                        referencia_id=doc.id, excluir_usuario=request.user,
                    )
                    messages.success(request, f'Documento "{nombre}" subido exitosamente.')

        elif action == 'delete':
            doc_id = request.POST.get('doc_id')
            try:
                doc = Documento.objects.get(id=doc_id, grupo=grupo, activo=True)
                if doc.usuario != request.user:
                    messages.error(request, 'Solo el autor puede eliminar el documento.')
                else:
                    doc.activo = False
                    doc.save()
                    messages.success(request, 'Documento eliminado.')
            except Documento.DoesNotExist:
                messages.error(request, 'Documento no encontrado.')

        return redirect('documents-group', group_id=group_id)

    documentos = (
        Documento.objects.filter(grupo=grupo, activo=True)
        .select_related('usuario').order_by('-created_at')
    )
    return render(request, 'documents/index.html', {
        'grupo': grupo,
        'documentos': documentos,
        'multi_grupo': _get_memberships(request.user).count() > 1,
    })
