from django.contrib import admin
from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'usuario', 'leida', 'created_at']
    list_filter = ['tipo', 'leida']
    search_fields = ['titulo', 'usuario__username']
