import uuid
from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    TIPO_GASTO = 'gasto'
    TIPO_INGRESO = 'ingreso'
    TIPO_PRESUPUESTO = 'presupuesto'
    TIPO_ANUNCIO = 'anuncio'
    TIPO_INVITACION = 'invitacion'
    TIPO_GASTO_COMPARTIDO = 'gasto_compartido'
    TIPO_CHOICES = [
        (TIPO_GASTO, 'Gasto'),
        (TIPO_INGRESO, 'Ingreso'),
        (TIPO_PRESUPUESTO, 'Presupuesto'),
        (TIPO_ANUNCIO, 'Anuncio'),
        (TIPO_INVITACION, 'Invitación'),
        (TIPO_GASTO_COMPARTIDO, 'Gasto compartido'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=500)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    referencia_id = models.UUIDField(null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
    )
    leida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificaciones'
        indexes = [
            models.Index(fields=['usuario', 'leida']),
            models.Index(fields=['usuario', '-created_at']),
        ]

    def __str__(self):
        return f"{self.tipo}: {self.titulo[:50]}"
