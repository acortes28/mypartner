from django.db.models import Sum
from rest_framework import serializers
from .models import (
    AporteAhorro, Concepto, DivisionPresupuesto, GastoCompartido,
    MetaAhorro, Movimiento, RegistroPresupuesto, ReplicaGrupal, Tarjeta,
)


class ConceptoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concepto
        fields = ['id', 'nombre', 'tipo', 'created_at']
        read_only_fields = ['id', 'created_at']


class MovimientoSerializer(serializers.ModelSerializer):
    concepto_nombre = serializers.SerializerMethodField()
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    es_replica = serializers.SerializerMethodField()
    tarjeta_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Movimiento
        fields = [
            'id', 'tipo', 'nombre', 'detalle', 'monto',
            'concepto', 'concepto_nombre', 'usuario_username',
            'es_replica', 'fecha_hora', 'tarjeta', 'tarjeta_nombre', 'cuotas', 'created_at',
        ]
        read_only_fields = ['id', 'usuario_username', 'es_replica', 'created_at']

    def get_concepto_nombre(self, obj):
        if obj.concepto and obj.concepto.activo:
            return obj.concepto.nombre
        return 'Desconocido'

    def get_es_replica(self, obj):
        return obj.origen_replica.exists()

    def get_tarjeta_nombre(self, obj):
        return obj.tarjeta.nombre if obj.tarjeta else None


class MovimientoCreateSerializer(serializers.ModelSerializer):
    tarjeta = serializers.PrimaryKeyRelatedField(
        queryset=Tarjeta.objects.filter(activa=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Movimiento
        fields = ['tipo', 'nombre', 'detalle', 'monto', 'concepto', 'fecha_hora', 'tarjeta', 'cuotas']

    def validate_concepto(self, value):
        if value and not value.activo:
            raise serializers.ValidationError('El concepto seleccionado no está disponible.')
        return value

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto debe ser mayor a cero.')
        return value


class ReplicaGrupalSerializer(serializers.ModelSerializer):
    grupo_nombre = serializers.CharField(source='grupo.nombre', read_only=True)
    movimiento_grupo_id = serializers.UUIDField(source='movimiento_grupo.id', read_only=True)

    class Meta:
        model = ReplicaGrupal
        fields = ['id', 'grupo_nombre', 'movimiento_grupo_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class DivisionPresupuestoSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    grupo_nombre = serializers.CharField(source='grupo.nombre', read_only=True)
    porcentaje = serializers.FloatField(read_only=True)

    class Meta:
        model = DivisionPresupuesto
        fields = ['id', 'usuario_username', 'grupo_nombre', 'monto', 'porcentaje', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegistroPresupuestoSerializer(serializers.ModelSerializer):
    concepto_nombre = serializers.CharField(source='concepto.nombre', read_only=True)
    usuario_username = serializers.SerializerMethodField()
    divisiones = DivisionPresupuestoSerializer(many=True, read_only=True)

    class Meta:
        model = RegistroPresupuesto
        fields = [
            'id', 'tipo', 'concepto', 'concepto_nombre', 'nombre',
            'detalle', 'monto', 'fecha', 'periodicidad', 'fecha_fin',
            'usuario_username', 'divisiones', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_usuario_username(self, obj):
        return obj.usuario.username if obj.usuario else None


class RegistroPresupuestoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroPresupuesto
        fields = ['monto']

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto debe ser mayor a cero.')
        return value


class FinanciasDashboardSerializer(serializers.Serializer):
    gasto_acumulado_mensual = serializers.IntegerField()
    saldo_restante = serializers.IntegerField()
    desviacion_presupuesto = serializers.IntegerField()
    grafico_torta = serializers.ListField(child=serializers.DictField())
    ultimos_movimientos = MovimientoSerializer(many=True)


# ── Nuevos serializers ──────────────────────────────────────────────────────

class GastoCompartidoSerializer(serializers.ModelSerializer):
    movimiento_nombre = serializers.SerializerMethodField()
    concepto_nombre = serializers.SerializerMethodField()
    movimiento_id = serializers.SerializerMethodField()
    grupo_nombre = serializers.CharField(source='grupo.nombre', read_only=True)
    usuario_acreedor_username = serializers.CharField(source='usuario_acreedor.username', read_only=True)
    usuario_deudor_username = serializers.CharField(source='usuario_deudor.username', read_only=True)

    class Meta:
        model = GastoCompartido
        fields = [
            'id', 'monto_pendiente', 'pagado', 'created_at',
            'movimiento_id', 'movimiento_nombre', 'concepto_nombre',
            'grupo', 'grupo_nombre',
            'usuario_acreedor', 'usuario_acreedor_username',
            'usuario_deudor', 'usuario_deudor_username',
        ]
        read_only_fields = fields

    def get_movimiento_nombre(self, obj):
        return obj.movimiento.nombre if obj.movimiento else 'Liquidación de deudas'

    def get_concepto_nombre(self, obj):
        if obj.movimiento and obj.movimiento.concepto:
            return obj.movimiento.concepto.nombre
        if not obj.movimiento:
            return 'Liquidación de deuda'
        return 'sin concepto'

    def get_movimiento_id(self, obj):
        return str(obj.movimiento_id) if obj.movimiento_id else None


class TarjetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarjeta
        fields = ['id', 'nombre', 'tipo', 'banco', 'cupo_total', 'cupo_usado', 'activa', 'created_at']
        read_only_fields = ['id', 'activa', 'created_at']


class TarjetaCreateSerializer(serializers.ModelSerializer):
    cupo_total = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    cupo_usado = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    class Meta:
        model = Tarjeta
        fields = ['nombre', 'tipo', 'banco', 'cupo_total', 'cupo_usado']

    def validate(self, data):
        if data.get('tipo') == Tarjeta.TIPO_DEBITO:
            data['cupo_total'] = None
            data['cupo_usado'] = None
        cupo_total = data.get('cupo_total')
        cupo_usado = data.get('cupo_usado')
        if cupo_total is not None and cupo_usado is not None and cupo_usado > cupo_total:
            raise serializers.ValidationError(
                {'cupo_usado': 'El cupo utilizado no puede ser mayor al cupo total.'}
            )
        return data


class AporteAhorroSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = AporteAhorro
        fields = ['id', 'monto', 'fecha', 'usuario_username', 'created_at']
        read_only_fields = ['id', 'fecha', 'usuario_username', 'created_at']


class MetaAhorroSerializer(serializers.ModelSerializer):
    ahorrado = serializers.SerializerMethodField()
    porcentaje = serializers.SerializerMethodField()
    completada = serializers.SerializerMethodField()

    class Meta:
        model = MetaAhorro
        fields = [
            'id', 'nombre', 'monto_objetivo', 'fecha_limite', 'tipo',
            'activa', 'ahorrado', 'porcentaje', 'completada', 'created_at',
        ]
        read_only_fields = ['id', 'tipo', 'activa', 'created_at']

    def get_ahorrado(self, obj):
        return obj.aportes.aggregate(t=Sum('monto'))['t'] or 0

    def get_porcentaje(self, obj):
        return obj.porcentaje_completado()

    def get_completada(self, obj):
        return obj.completada()


class MetaAhorroCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaAhorro
        fields = ['nombre', 'monto_objetivo', 'fecha_limite']

    def validate_monto_objetivo(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto objetivo debe ser mayor a cero.')
        return value


# ── Serializers de input (validación de campos no-modelo) ─────────────────

class DivisionInputSerializer(serializers.Serializer):
    usuario_id = serializers.UUIDField()
    monto = serializers.IntegerField(min_value=1)


class PresupuestoPersonalCreateSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=RegistroPresupuesto.TIPO_CHOICES)
    concepto = serializers.PrimaryKeyRelatedField(queryset=Concepto.objects.filter(activo=True))
    nombre = serializers.CharField(max_length=255)
    detalle = serializers.CharField(default='', allow_blank=True, required=False)
    monto = serializers.IntegerField(min_value=1)
    fecha = serializers.DateField()
    periodicidad = serializers.ChoiceField(
        choices=RegistroPresupuesto.PERIODICIDAD_CHOICES,
        default=RegistroPresupuesto.PERIODICIDAD_PUNTUAL,
        required=False,
    )
    fecha_fin = serializers.DateField(required=False, allow_null=True)
    dividir_presupuesto = serializers.BooleanField(default=False, required=False)
    grupo_division_id = serializers.UUIDField(required=False, allow_null=True)
    divisiones = DivisionInputSerializer(many=True, default=list, required=False)


class SplitDistribucionSerializer(serializers.Serializer):
    usuario_id = serializers.UUIDField()
    monto = serializers.IntegerField(min_value=1)


class SplitConfirmInputSerializer(serializers.Serializer):
    grupo_id = serializers.UUIDField()
    monto_total = serializers.IntegerField(min_value=1)
    concepto_nombre = serializers.CharField(max_length=255, default='División de cuenta', required=False)
    payer_id = serializers.UUIDField(required=False, allow_null=True)
    distribuciones = SplitDistribucionSerializer(many=True)
