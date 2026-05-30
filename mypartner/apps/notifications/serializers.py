from rest_framework import serializers
from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['id', 'titulo', 'tipo', 'referencia_id', 'leida', 'created_at']
        read_only_fields = fields
