import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from apps.groups.models import GrupoMiembro
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from .models import Documento, ALLOWED_EXTENSIONS


def _get_grupo(user):
    m = GrupoMiembro.objects.filter(usuario=user, grupo__activo=True).select_related('grupo').first()
    return m.grupo if m else None


@login_required
def documents_view(request):
    grupo = _get_grupo(request.user)
    if not grupo:
        messages.info(request, 'Para acceder a este módulo necesitas pertenecer a un grupo.')
        return redirect('group-manage')

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

        return redirect('documents-index')

    documentos = (
        Documento.objects.filter(grupo=grupo, activo=True)
        .select_related('usuario').order_by('-created_at')
    )
    return render(request, 'documents/index.html', {'grupo': grupo, 'documentos': documentos})
