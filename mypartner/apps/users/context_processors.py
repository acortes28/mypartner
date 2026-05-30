from apps.groups.models import GrupoMiembro
from apps.notifications.models import Notificacion


def user_context(request):
    if not request.user.is_authenticated:
        return {}

    membership = (
        GrupoMiembro.objects
        .filter(usuario=request.user, grupo__activo=True)
        .select_related('grupo')
        .first()
    )

    unread_qs = (
        Notificacion.objects
        .filter(usuario=request.user, leida=False)
        .order_by('-created_at')
    )

    return {
        'user_group': membership.grupo if membership else None,
        'user_role': membership.rol if membership else None,
        'unread_notifications_count': unread_qs.count(),
        'recent_notifications': list(unread_qs[:5]),
    }
