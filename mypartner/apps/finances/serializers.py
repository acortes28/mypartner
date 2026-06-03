from rest_framework import serializers
from .models import Concepto, DivisionPresupuesto, Movimiento, RegistroPresupuesto, ReplicaGrupal


class ConceptoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concepto
        fields = ['id', 'nombre', 'tipo', 'created_at']
        read_only_fields = ['id', 'created_at']


class MovimientoSerializer(serializers.ModelSerializer):
    concepto_nombre = serializers.SerializerMethodField()
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    es_replica = serializers.SerializerMethodField()

    class Meta:
        model = Movimiento
        fields = [
            'id', 'tipo', 'nombre', 'detalle', 'monto',
            'concepto', 'concepto_nombre', 'usuario_username',
            'es_replica', 'fecha_hora', 'created_at',
        ]
        read_only_fields = ['id', 'usuario_username', 'es_replica', 'created_at']

    def get_concepto_nombre(self, obj):
        if obj.concepto and obj.concepto.activo:
            return obj.concepto.nombre
        return 'Desconocido'

    def get_es_replica(self, obj):
        return obj.origen_replica.exists()


class MovimientoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        fields = ['tipo', 'nombre', 'detalle', 'monto', 'concepto', 'fecha_hora']

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
