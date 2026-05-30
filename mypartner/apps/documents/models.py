import uuid
from django.conf import settings
from django.db import models


ALLOWED_EXTENSIONS = ['pdf', 'csv', 'xlsx', 'png']


def document_upload_path(instance, filename):
    return f"documents/{instance.grupo_id}/{filename}"


class Documento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, default='')
    archivo = models.FileField(upload_to=document_upload_path)
    tipo_archivo = models.CharField(max_length=10)
    tamano_bytes = models.PositiveIntegerField(null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='documentos',
    )
    grupo = models.ForeignKey(
        'groups.Grupo', on_delete=models.CASCADE, related_name='documentos'
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documentos'

    def __str__(self):
        return self.nombre
