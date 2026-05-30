from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from apps.notifications.models import Notificacion
from apps.users.models import User
from .models import Grupo, GrupoMiembro, Invitacion


def _get_membership(user):
    return (
        GrupoMiembro.objects
        .filter(usuario=user, grupo__activo=True)
        .select_related('grupo')
        .first()
    )


@login_required
def group_manage_view(request):
    membership = _get_membership(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_group':
            if membership:
                messages.error(request, 'Ya perteneces a un grupo.')
                return redirect('group-manage')
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            if not nombre:
                messages.error(request, 'El nombre del grupo es obligatorio.')
                return redirect('group-manage')
            grupo = Grupo.objects.create(nombre=nombre, descripcion=descripcion)
            GrupoMiembro.objects.create(usuario=request.user, grupo=grupo, rol=GrupoMiembro.ROL_ADMIN)
            messages.success(request, f'Grupo "{nombre}" creado exitosamente.')
            return redirect('group-manage')

        if not membership:
            return redirect('group-manage')
        grupo = membership.grupo

        if action == 'invite_member':
            if membership.rol != GrupoMiembro.ROL_ADMIN:
                messages.error(request, 'No tienes permisos para invitar miembros.')
                return redirect('group-manage')
            username = request.POST.get('username', '').strip()
            comentario = request.POST.get('comentario', '').strip()
            try:
                receptor = User.objects.get(username=username)
            except User.DoesNotExist:
                messages.error(request, f'No se encontró el usuario "{username}".')
                return redirect('group-manage')
            if GrupoMiembro.objects.filter(usuario=receptor, grupo=grupo).exists():
                messages.error(request, 'Ese usuario ya es miembro del grupo.')
                return redirect('group-manage')
            una_hora = timezone.now() - timedelta(hours=1)
            if Invitacion.objects.filter(
                emisor=request.user, receptor=receptor,
                estado=Invitacion.ESTADO_RECHAZADA, updated_at__gte=una_hora
            ).count() >= 2:
                messages.error(request, 'No puedes enviar invitaciones a este usuario por 24 horas.')
                return redirect('group-manage')
            inv = Invitacion.objects.create(
                emisor=request.user, receptor=receptor, grupo=grupo, comentario=comentario
            )
            Notificacion.objects.create(
                titulo=f'{request.user.username} te ha invitado al grupo {grupo.nombre}',
                tipo=Notificacion.TIPO_INVITACION,
                referencia_id=inv.id,
                usuario=receptor,
            )
            messages.success(request, f'Invitación enviada a {username}.')
            return redirect('group-manage')

        if action == 'remove_member':
            if membership.rol != GrupoMiembro.ROL_ADMIN:
                messages.error(request, 'No tienes permisos.')
                return redirect('group-manage')
            usuario_id = request.POST.get('usuario_id')
            if str(request.user.id) == usuario_id:
                messages.error(request, 'No puedes expulsarte a ti mismo.')
                return redirect('group-manage')
            try:
                m = GrupoMiembro.objects.get(usuario_id=usuario_id, grupo=grupo)
                username = m.usuario.username
                m.delete()
                messages.success(request, f'{username} fue expulsado del grupo.')
            except GrupoMiembro.DoesNotExist:
                messages.error(request, 'Miembro no encontrado.')
            return redirect('group-manage')

        if action == 'set_role':
            if membership.rol != GrupoMiembro.ROL_ADMIN:
                messages.error(request, 'No tienes permisos.')
                return redirect('group-manage')
            usuario_id = request.POST.get('usuario_id')
            nuevo_rol = request.POST.get('rol')
            if nuevo_rol not in (GrupoMiembro.ROL_ADMIN, GrupoMiembro.ROL_MIEMBRO):
                messages.error(request, 'Rol inválido.')
                return redirect('group-manage')
            try:
                m = GrupoMiembro.objects.get(usuario_id=usuario_id, grupo=grupo)
                m.rol = nuevo_rol
                m.save()
                label = 'ahora es administrador' if nuevo_rol == GrupoMiembro.ROL_ADMIN else 'ya no es administrador'
                messages.success(request, f'{m.usuario.username} {label}.')
            except GrupoMiembro.DoesNotExist:
                messages.error(request, 'Miembro no encontrado.')
            return redirect('group-manage')

        if action == 'leave_group':
            if membership.rol == GrupoMiembro.ROL_ADMIN:
                other_admins = GrupoMiembro.objects.filter(
                    grupo=grupo, rol=GrupoMiembro.ROL_ADMIN
                ).exclude(usuario=request.user)
                if not other_admins.exists():
                    messages.error(request, 'Debes asignar otro administrador antes de abandonar.')
                    return redirect('group-manage')
            membership.delete()
            messages.success(request, 'Abandonaste el grupo exitosamente.')
            return redirect('group-manage')

        if action == 'delete_group':
            if membership.rol != GrupoMiembro.ROL_ADMIN:
                messages.error(request, 'No tienes permisos.')
                return redirect('group-manage')
            nombre = grupo.nombre
            grupo.activo = False
            grupo.save()
            messages.success(request, f'El grupo "{nombre}" fue eliminado.')
            return redirect('group-manage')

    miembros = []
    if membership:
        miembros = (
            GrupoMiembro.objects
            .filter(grupo=membership.grupo)
            .select_related('usuario')
            .order_by('rol', 'usuario__username')
        )

    return render(request, 'groups/manage.html', {
        'membership': membership,
        'miembros': miembros,
    })


@login_required
def invitation_view(request, invitation_id):
    inv = get_object_or_404(
        Invitacion, id=invitation_id, receptor=request.user, estado=Invitacion.ESTADO_PENDIENTE
    )
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            if not inv.grupo.activo:
                messages.error(request, 'El grupo ya no existe.')
                return redirect('main-menu')
            GrupoMiembro.objects.filter(usuario=request.user).delete()
            GrupoMiembro.objects.create(usuario=request.user, grupo=inv.grupo, rol=GrupoMiembro.ROL_MIEMBRO)
            inv.estado = Invitacion.ESTADO_ACEPTADA
            inv.save()
            messages.success(request, f'Te uniste al grupo "{inv.grupo.nombre}".')
            return redirect('main-menu')
        elif action == 'reject':
            inv.estado = Invitacion.ESTADO_RECHAZADA
            inv.save()
            messages.info(request, 'Invitación rechazada.')
            return redirect('main-menu')
    return render(request, 'groups/invitation.html', {'invitacion': inv})
