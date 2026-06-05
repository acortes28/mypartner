import uuid
from django.conf import settings
from django.db import models
from django.db.models import Sum

BANCOS_CHILE = [
    'Banco de Chile', 'Banco Santander Chile', 'Banco BCI', 'Banco Estado',
    'Banco Scotiabank Chile', 'Banco Itaú Chile', 'Banco Security',
    'Banco BICE', 'Banco Consorcio', 'Banco Internacional',
    'Banco Falabella', 'Banco Ripley', 'Coopeuch',
    'HSBC Bank Chile', 'Mercado Pago', 'MACH', 'Tenpo', 'Chek',
]


class Concepto(models.Model):
    TIPO_GASTO = 'Gasto'
    TIPO_INGRESO = 'Ingreso'
    TIPO_CHOICES = [(TIPO_GASTO, 'Gasto'), (TIPO_INGRESO, 'Ingreso')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conceptos',
        null=True,
        blank=True,
    )
    grupo = models.ForeignKey(
        'groups.Grupo',
        on_delete=models.CASCADE,
        related_name='conceptos',
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conceptos'
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(usuario__isnull=False, grupo__isnull=True) |
                    models.Q(usuario__isnull=True, grupo__isnull=False)
                ),
                name='concepto_contexto_exclusivo',
            ),
            models.UniqueConstraint(
                fields=['nombre', 'usuario'],
                condition=models.Q(activo=True, grupo__isnull=True),
                name='concepto_nombre_usuario_personal_unique',
            ),
            models.UniqueConstraint(
                fields=['nombre', 'grupo'],
                condition=models.Q(activo=True, usuario__isnull=True),
                name='concepto_nombre_grupo_unique',
            ),
        ]
        indexes = [
            models.Index(fields=['usuario', 'tipo'], name='idx_concepto_usuario_tipo'),
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
        'groups.Grupo',
        on_delete=models.CASCADE,
        related_name='movimientos',
        null=True,
        blank=True,
    )
    fecha_hora = models.DateTimeField()
    tarjeta = models.ForeignKey(
        'Tarjeta',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimientos',
    )
    cuotas = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movimientos'
        indexes = [
            models.Index(fields=['usuario', '-fecha_hora'], name='idx_mov_usuario_fecha'),
            models.Index(fields=['grupo', '-fecha_hora'], name='idx_mov_grupo_fecha'),
            models.Index(fields=['usuario', 'tipo'], name='idx_mov_usuario_tipo'),
            models.Index(fields=['grupo', 'tipo'], name='idx_mov_grupo_tipo'),
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
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presupuestos',
        null=True,
        blank=True,
    )
    grupo = models.ForeignKey(
        'groups.Grupo',
        on_delete=models.CASCADE,
        related_name='presupuestos',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'presupuesto'
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(usuario__isnull=False, grupo__isnull=True) |
                    models.Q(usuario__isnull=True, grupo__isnull=False)
                ),
                name='presupuesto_contexto_exclusivo',
            ),
        ]

    def __str__(self):
        return f"Presupuesto {self.nombre} - ${self.monto:,}"


class GastoCompartido(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movimiento = models.ForeignKey(
        Movimiento, on_delete=models.CASCADE, related_name='compartidos',
        null=True, blank=True,
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


class ReplicaGrupal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movimiento_personal = models.ForeignKey(
        Movimiento,
        on_delete=models.CASCADE,
        related_name='replicas',
    )
    movimiento_grupo = models.ForeignKey(
        Movimiento,
        on_delete=models.CASCADE,
        related_name='origen_replica',
    )
    grupo = models.ForeignKey(
        'groups.Grupo',
        on_delete=models.CASCADE,
        related_name='replicas',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'replicas_grupales'
        unique_together = ('movimiento_personal', 'grupo')

    def __str__(self):
        return f"Réplica de {self.movimiento_personal_id} en {self.grupo.nombre}"


class DivisionPresupuesto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registro_presupuesto = models.ForeignKey(
        RegistroPresupuesto,
        on_delete=models.CASCADE,
        related_name='divisiones',
    )
    grupo = models.ForeignKey(
        'groups.Grupo',
        on_delete=models.CASCADE,
        related_name='divisiones_presupuesto',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='divisiones_presupuesto',
    )
    monto = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'divisiones_presupuesto'
        unique_together = ('registro_presupuesto', 'usuario')
        indexes = [
            models.Index(fields=['registro_presupuesto'], name='idx_division_presupuesto'),
            models.Index(fields=['usuario', 'grupo'], name='idx_division_usuario_grupo'),
        ]

    def __str__(self):
        return f"{self.usuario.username}: ${self.monto:,} de {self.registro_presupuesto.nombre}"

    @property
    def porcentaje(self):
        total = self.registro_presupuesto.monto
        return round(self.monto / total * 100, 2) if total else 0


class MetaAhorro(models.Model):
    TIPO_PERSONAL = 'personal'
    TIPO_GRUPAL = 'grupal'
    TIPO_CHOICES = [(TIPO_PERSONAL, 'Personal'), (TIPO_GRUPAL, 'Grupal')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255)
    monto_objetivo = models.PositiveIntegerField()
    fecha_limite = models.DateField(null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='metas_ahorro',
        null=True, blank=True,
    )
    grupo = models.ForeignKey(
        'groups.Grupo',
        on_delete=models.CASCADE,
        related_name='metas_ahorro',
        null=True, blank=True,
    )
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'metas_ahorro'
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(usuario__isnull=False, grupo__isnull=True) |
                    models.Q(usuario__isnull=True, grupo__isnull=False)
                ),
                name='meta_ahorro_contexto_exclusivo',
            ),
        ]

    def __str__(self):
        return f"{self.nombre} (${self.monto_objetivo:,})"

    def monto_ahorrado(self):
        return self.aportes.aggregate(t=Sum('monto'))['t'] or 0

    def porcentaje_completado(self):
        if not self.monto_objetivo:
            return 0
        return min(100, round((self.monto_ahorrado() / self.monto_objetivo) * 100))

    def completada(self):
        return self.monto_ahorrado() >= self.monto_objetivo


class AporteAhorro(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meta = models.ForeignKey(
        MetaAhorro, on_delete=models.CASCADE, related_name='aportes'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='aportes_ahorro',
    )
    movimiento = models.ForeignKey(
        'Movimiento',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='aportes_ahorro',
    )
    monto = models.IntegerField()
    fecha = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'aportes_ahorro'
        indexes = [
            models.Index(fields=['meta', '-fecha'], name='idx_aporte_meta_fecha'),
        ]

    def __str__(self):
        return f"{self.usuario.username}: ${self.monto:,} → {self.meta.nombre}"


class Tarjeta(models.Model):
    TIPO_DEBITO = 'Debito'
    TIPO_CREDITO = 'Credito'
    TIPO_CHOICES = [
        (TIPO_DEBITO, 'Débito'),
        (TIPO_CREDITO, 'Crédito'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    banco = models.CharField(max_length=100)
    cupo_total = models.PositiveIntegerField(null=True, blank=True)
    cupo_usado = models.PositiveIntegerField(null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tarjetas',
    )
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tarjetas'

    def __str__(self):
        return f"{self.nombre} — {self.banco} ({self.tipo})"
