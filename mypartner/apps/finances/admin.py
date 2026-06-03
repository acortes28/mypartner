from django.contrib import admin
from .models import Concepto, DivisionPresupuesto, GastoCompartido, Movimiento, RegistroPresupuesto, ReplicaGrupal


@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'usuario', 'grupo', 'activo', 'created_at']
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre', 'usuario__username', 'grupo__nombre']


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'monto', 'usuario', 'grupo', 'fecha_hora']
    list_filter = ['tipo']
    search_fields = ['nombre', 'usuario__username']
    ordering = ['-fecha_hora']


@admin.register(RegistroPresupuesto)
class RegistroPresupuestoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'monto', 'concepto', 'usuario', 'grupo', 'fecha']
    list_filter = ['tipo']
    search_fields = ['nombre', 'usuario__username', 'grupo__nombre']


@admin.register(GastoCompartido)
class GastoCompartidoAdmin(admin.ModelAdmin):
    list_display = ['movimiento', 'usuario_acreedor', 'usuario_deudor', 'monto_pendiente', 'pagado', 'grupo']
    list_filter = ['pagado']


@admin.register(ReplicaGrupal)
class ReplicaGrupalAdmin(admin.ModelAdmin):
    list_display = ['movimiento_personal', 'grupo', 'created_at']


@admin.register(DivisionPresupuesto)
class DivisionPresupuestoAdmin(admin.ModelAdmin):
    list_display = ['registro_presupuesto', 'usuario', 'grupo', 'monto', 'created_at']
