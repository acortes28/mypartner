import uuid
from django.conf import settings
from django.db import models


class Concepto(models.Model):
    TIPO_GASTO = 'Gasto'
    TIPO_INGRESO = 'Ingreso'
    TIPO_CHOICES = [(TIPO_GASTO, 'Gasto'), (TIPO_INGRESO, 'Ingreso')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    grupo = models.ForeignKey(
        'groups.Grupo', on_delete=models.CASCADE, related_name='conceptos'
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conceptos'
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'grupo'],
                condition=models.Q(activo=True),
                name='conceptos_nombre_grupo_activo_unique',
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"


class Movimiento(models.Model):
    TIPO_GASTO = 'Gasto'
    TIPO_INGRESO = 'Ingreso'
    TIPO_CHOICES = [(TIPO_GASTO, 'Gasto'), (TIPO_INGRESO, 'Ingreso')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=255)
    detalle = models.TextField(blank=True, default='')
    monto = models.PositiveIntegerField()
    concepto = models.ForeignKey(
        Concepto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimientos',
    )
    grupo = models.ForeignKey(
        'groups.Grupo', on_delete=models.CASCADE, related_name='movimientos'
    )
    fecha_hora = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movimientos'
        indexes = [
            models.Index(fields=['grupo', '-fecha_hora']),
            models.Index(fields=['grupo', 'tipo']),
        ]

    def __str__(self):
        return f"{self.tipo}: {self.nombre} - ${self.monto:,}"


class RegistroPresupuesto(models.Model):
    TIPO_GASTO = 'Gasto'
    TIPO_INGRESO = 'Ingreso'
    TIPO_CHOICES = [(TIPO_GASTO, 'Gasto'), (TIPO_INGRESO, 'Ingreso')]

    PERIODICIDAD_PUNTUAL = 'Puntual'
    PERIODICIDAD_MENSUAL = 'Mensual'
    PERIODICIDAD_ANUAL = 'Anual'
    PERIODICIDAD_CHOICES = [
        (PERIODICIDAD_PUNTUAL, 'Puntual'),
        (PERIODICIDAD_MENSUAL, 'Mensual'),
        (PERIODICIDAD_ANUAL, 'Anual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    periodicidad = models.CharField(
        max_length=10, choices=PERIODICIDAD_CHOICES, default=PERIODICIDAD_PUNTUAL
    )
    fecha_fin = models.DateField(null=True, blank=True)
    concepto = models.ForeignKey(
        Concepto, on_delete=models.PROTECT, related_name='presupuestos'
    )
    nombre = models.CharField(max_length=255)
    detalle = models.TextField(blank=True, default='')
    monto = models.PositiveIntegerField()
    fecha = models.DateField()
    grupo = models.ForeignKey(
        'groups.Grupo', on_delete=models.CASCADE, related_name='presupuestos'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'presupuesto'

    def __str__(self):
        return f"Presupuesto {self.nombre} - ${self.monto:,}"


class GastoCompartido(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movimiento = models.ForeignKey(
        Movimiento, on_delete=models.CASCADE, related_name='compartidos'
    )
    usuario_acreedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gastos_acreedor'
    )
    usuario_deudor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gastos_deudor'
    )
    monto_pendiente = models.PositiveIntegerField()
    pagado = models.BooleanField(default=False)
    grupo = models.ForeignKey(
        'groups.Grupo', on_delete=models.CASCADE, related_name='gastos_compartidos'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gastos_compartidos'

    def __str__(self):
        return f"{self.usuario_acreedor} → {self.usuario_deudor}: ${self.monto_pendiente:,}"
