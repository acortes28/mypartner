from rest_framework import serializers
from .models import Grupo, GrupoMiembro, Invitacion
from apps.users.models import User


class GrupoMiembroSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', read_only=True)
    nombre = serializers.CharField(source='usuario.first_name', read_only=True)
    apellido = serializers.CharField(source='usuario.last_name', read_only=True)
    usuario_id = serializers.UUIDField(source='usuario.id', read_only=True)

    class Meta:
        model = GrupoMiembro
        fields = ['usuario_id', 'username', 'nombre', 'apellido', 'rol', 'created_at']


class GrupoSerializer(serializers.ModelSerializer):
    miembros = GrupoMiembroSerializer(many=True, read_only=True)

    class Meta:
        model = Grupo
        fields = ['id', 'nombre', 'descripcion', 'miembros', 'created_at']
        read_only_fields = ['id', 'created_at']


class CreateGrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grupo
        fields = ['nombre', 'descripcion']


class InvitarUsuarioSerializer(serializers.Serializer):
    username = serializers.CharField()
    comentario = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_username(self, value):
        try:
            return User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('No se encontró un usuario con ese nombre de usuario.')


class RemoverMiembroSerializer(serializers.Serializer):
    usuario_id = serializers.UUIDField()


class SetRolSerializer(serializers.Serializer):
    usuario_id = serializers.UUIDField()
    rol = serializers.ChoiceField(choices=GrupoMiembro.ROL_CHOICES)


class InvitacionSerializer(serializers.ModelSerializer):
    grupo_nombre = serializers.CharField(source='grupo.nombre', read_only=True)
    grupo_id = serializers.UUIDField(source='grupo.id', read_only=True)
    emisor_username = serializers.CharField(source='emisor.username', read_only=True)

    class Meta:
        model = Invitacion
        fields = ['id', 'grupo_id', 'grupo_nombre', 'emisor_username', 'comentario', 'estado', 'created_at']
