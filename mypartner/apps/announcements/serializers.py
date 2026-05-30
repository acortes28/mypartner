from rest_framework import serializers
from .models import Anuncio, Comentario


class ComentarioSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Comentario
        fields = ['id', 'contenido', 'usuario_username', 'created_at']
        read_only_fields = ['id', 'usuario_username', 'created_at']


class AnuncioListSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Anuncio
        fields = ['id', 'nombre', 'descripcion', 'usuario_username', 'created_at']
        read_only_fields = fields


class AnuncioDetailSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    comentarios = ComentarioSerializer(many=True, read_only=True)

    class Meta:
        model = Anuncio
        fields = ['id', 'nombre', 'descripcion', 'usuario_username', 'comentarios', 'created_at']
        read_only_fields = fields


class AnuncioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anuncio
        fields = ['nombre', 'descripcion']


class ComentarioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comentario
        fields = ['contenido']
