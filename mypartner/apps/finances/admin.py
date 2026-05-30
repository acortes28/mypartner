from django.contrib import admin
from .models import Concepto, Movimiento, RegistroPresupuesto


@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'grupo', 'activo', 'created_at']
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre', 'grupo__nombre']


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'monto', 'usuario', 'grupo', 'fecha_hora']
    list_filter = ['tipo']
    search_fields = ['nombre', 'usuario__username']
    ordering = ['-fecha_hora']


@admin.register(RegistroPresupuesto)
class RegistroPresupuestoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'monto', 'concepto', 'grupo', 'fecha']
    list_filter = ['tipo']
    search_fields = ['nombre', 'grupo__nombre']
