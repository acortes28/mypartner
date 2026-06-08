import logging

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notificacion
from apps.groups.models import GrupoMiembro

logger = logging.getLogger(__name__)


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


def _send_push(usuario_id, titulo, tipo):
    """Envía push notification vía OneSignal REST API. Falla silenciosamente."""
    app_id = getattr(settings, 'ONESIGNAL_APP_ID', '')
    api_key = getattr(settings, 'ONESIGNAL_REST_API_KEY', '')
    if not app_id or not api_key:
        return

    try:
        requests.post(
            'https://onesignal.com/api/v1/notifications',
            headers={
                'Authorization': f'Key {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'app_id': app_id,
                'include_aliases': {'external_id': [str(usuario_id)]},
                'target_channel': 'push',
                'contents': {'es': titulo, 'en': titulo},
                'data': {'tipo': tipo.upper()},
            },
            timeout=5,
        )
    except Exception as exc:
        logger.warning('OneSignal push failed for user %s: %s', usuario_id, exc)


@receiver(post_save, sender=Notificacion)
def _on_notificacion_created(sender, instance, created, **kwargs):
    if created:
        _send_push(instance.usuario_id, instance.titulo, instance.tipo)
