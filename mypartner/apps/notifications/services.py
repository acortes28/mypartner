from .models import Notificacion
from apps.groups.models import GrupoMiembro


def crear_notificaciones_grupo(grupo, tipo, titulo, referencia_id=None, excluir_usuario=None):
    """Crea una notificación para todos los miembros activos del grupo."""
    miembros_qs = GrupoMiembro.objects.filter(grupo=grupo).select_related('usuario')
    if excluir_usuario:
        miembros_qs = miembros_qs.exclude(usuario=excluir_usuario)

    notificaciones = [
        Notificacion(
            titulo=titulo,
            tipo=tipo,
            referencia_id=referencia_id,
            usuario=m.usuario,
        )
        for m in miembros_qs
    ]
    Notificacion.objects.bulk_create(notificaciones)
