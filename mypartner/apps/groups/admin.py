from django.contrib import admin
from .models import Grupo, GrupoMiembro, Invitacion


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'created_at']
    list_filter = ['activo']
    search_fields = ['nombre']


@admin.register(GrupoMiembro)
class GrupoMiembroAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'grupo', 'rol', 'created_at']
    list_filter = ['rol']
    search_fields = ['usuario__username', 'grupo__nombre']


@admin.register(Invitacion)
class InvitacionAdmin(admin.ModelAdmin):
    list_display = ['emisor', 'receptor', 'grupo', 'estado', 'created_at']
    list_filter = ['estado']
    search_fields = ['emisor__username', 'receptor__username', 'grupo__nombre']
