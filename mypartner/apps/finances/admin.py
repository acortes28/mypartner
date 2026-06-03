from django.contrib import admin
from .models import (
    AporteAhorro, Concepto, DivisionPresupuesto, GastoCompartido,
    MetaAhorro, Movimiento, RegistroPresupuesto, ReplicaGrupal,
)


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


@admin.register(MetaAhorro)
class MetaAhorroAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'monto_objetivo', 'usuario', 'grupo', 'activa', 'fecha_limite', 'created_at']
    list_filter = ['tipo', 'activa']
    search_fields = ['nombre', 'usuario__username', 'grupo__nombre']


@admin.register(AporteAhorro)
class AporteAhorroAdmin(admin.ModelAdmin):
    list_display = ['meta', 'usuario', 'monto', 'fecha', 'created_at']
    search_fields = ['meta__nombre', 'usuario__username']
    ordering = ['-fecha']
