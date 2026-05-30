from django.contrib import admin
from .models import Documento


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_archivo', 'usuario', 'grupo', 'activo', 'created_at']
    list_filter = ['tipo_archivo', 'activo']
    search_fields = ['nombre', 'usuario__username']
