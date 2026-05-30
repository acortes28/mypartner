from django.contrib import admin
from .models import Anuncio, Comentario


@admin.register(Anuncio)
class AnuncioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'usuario', 'grupo', 'activo', 'created_at']
    list_filter = ['activo']
    search_fields = ['nombre', 'usuario__username']


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'anuncio', 'created_at']
    search_fields = ['usuario__username', 'anuncio__nombre']
