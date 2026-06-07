from rest_framework import serializers
from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    contexto_navegacion = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = ['id', 'titulo', 'tipo', 'referencia_id', 'leida', 'created_at', 'contexto_navegacion']
        read_only_fields = ['id', 'titulo', 'tipo', 'referencia_id', 'leida', 'created_at', 'contexto_navegacion']

    def get_contexto_navegacion(self, obj):
        ctx = {'tipo': obj.tipo}
        if not obj.referencia_id:
            return ctx
        ctx['referencia_id'] = str(obj.referencia_id)

        try:
            if obj.tipo == Notificacion.TIPO_ANUNCIO:
                from apps.announcements.models import Anuncio
                anuncio = Anuncio.objects.get(id=obj.referencia_id)
                ctx['grupo_id'] = str(anuncio.grupo_id)

            elif obj.tipo in (Notificacion.TIPO_GASTO, Notificacion.TIPO_INGRESO, Notificacion.TIPO_GASTO_COMPARTIDO):
                from apps.finances.models import Movimiento
                mov = Movimiento.objects.get(id=obj.referencia_id)
                if mov.grupo_id:
                    ctx['grupo_id'] = str(mov.grupo_id)

            elif obj.tipo == Notificacion.TIPO_PRESUPUESTO:
                from apps.finances.models import RegistroPresupuesto
                reg = RegistroPresupuesto.objects.get(id=obj.referencia_id)
                if reg.grupo_id:
                    ctx['grupo_id'] = str(reg.grupo_id)

            # TIPO_INVITACION: referencia_id es el UUID de la invitación — Flutter lo usa directo
        except Exception:
            pass

        return ctx
