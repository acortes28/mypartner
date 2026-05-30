import uuid
from django.conf import settings
from django.db import models


class Anuncio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='anuncios',
    )
    grupo = models.ForeignKey(
        'groups.Grupo', on_delete=models.CASCADE, related_name='anuncios'
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'anuncios'

    def __str__(self):
        return self.nombre


class Comentario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contenido = models.TextField()
    anuncio = models.ForeignKey(Anuncio, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='comentarios',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comentarios'

    def __str__(self):
        return f"Comentario de {self.usuario.username} en {self.anuncio.nombre}"
