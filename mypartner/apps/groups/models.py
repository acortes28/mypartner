import uuid
from django.conf import settings
from django.db import models


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(activo=True)


class Grupo(models.Model):
    ROL_CHOICES = [('admin', 'Admin'), ('miembro', 'Miembro')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default='')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'grupos'

    def __str__(self):
        return self.nombre


class GrupoMiembro(models.Model):
    ROL_ADMIN = 'admin'
    ROL_MIEMBRO = 'miembro'
    ROL_CHOICES = [(ROL_ADMIN, 'Admin'), (ROL_MIEMBRO, 'Miembro')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='miembros')
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default=ROL_MIEMBRO)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'grupo_miembros'
        unique_together = ('usuario', 'grupo')

    def __str__(self):
        return f"{self.usuario.username} en {self.grupo.nombre} ({self.rol})"


class Invitacion(models.Model):
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_ACEPTADA = 'aceptada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_ACEPTADA, 'Aceptada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invitaciones_enviadas',
    )
    receptor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invitaciones_recibidas',
    )
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='invitaciones')
    comentario = models.TextField(blank=True, default='')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invitaciones'

    def __str__(self):
        return f"Invitación de {self.emisor.username} a {self.receptor.username}"
