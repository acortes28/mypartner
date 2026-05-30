import os
from rest_framework import serializers
from .models import Documento, ALLOWED_EXTENSIONS


class DocumentoSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Documento
        fields = [
            'id', 'nombre', 'descripcion', 'archivo', 'tipo_archivo',
            'tamano_bytes', 'usuario_username', 'created_at',
        ]
        read_only_fields = ['id', 'tipo_archivo', 'tamano_bytes', 'usuario_username', 'created_at']


class DocumentoCreateSerializer(serializers.ModelSerializer):
    archivo = serializers.FileField()

    class Meta:
        model = Documento
        fields = ['nombre', 'descripcion', 'archivo']

    def validate_archivo(self, value):
        ext = os.path.splitext(value.name)[1].lstrip('.').lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f'Formato no permitido. Solo se aceptan: {", ".join(ALLOWED_EXTENSIONS)}.'
            )
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('El archivo no puede superar los 10 MB.')
        return value
