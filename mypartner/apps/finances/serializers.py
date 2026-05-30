from rest_framework import serializers
from .models import Concepto, Movimiento, RegistroPresupuesto


class ConceptoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concepto
        fields = ['id', 'nombre', 'tipo', 'created_at']
        read_only_fields = ['id', 'created_at']


class MovimientoSerializer(serializers.ModelSerializer):
    concepto_nombre = serializers.SerializerMethodField()
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Movimiento
        fields = [
            'id', 'tipo', 'nombre', 'detalle', 'monto',
            'concepto', 'concepto_nombre', 'usuario_username',
            'fecha_hora', 'created_at',
        ]
        read_only_fields = ['id', 'usuario_username', 'created_at']

    def get_concepto_nombre(self, obj):
        if obj.concepto and obj.concepto.activo:
            return obj.concepto.nombre
        return 'Desconocido'


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


class RegistroPresupuestoSerializer(serializers.ModelSerializer):
    concepto_nombre = serializers.CharField(source='concepto.nombre', read_only=True)

    class Meta:
        model = RegistroPresupuesto
        fields = [
            'id', 'tipo', 'concepto', 'concepto_nombre', 'nombre',
            'detalle', 'monto', 'fecha', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
