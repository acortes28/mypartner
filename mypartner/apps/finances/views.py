import csv
import io
from datetime import date

from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.groups.models import Grupo, GrupoMiembro
from apps.groups.permissions import IsGroupMember
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from .models import Concepto, GastoCompartido, Movimiento, RegistroPresupuesto, ReplicaGrupal
from .serializers import (
    ConceptoSerializer,
    MovimientoCreateSerializer,
    MovimientoSerializer,
    RegistroPresupuestoSerializer,
    RegistroPresupuestoUpdateSerializer,
    ReplicaGrupalSerializer,
)


def _get_grupo_or_404(group_id):
    try:
        return Grupo.objects.get(id=group_id, activo=True)
    except Grupo.DoesNotExist:
        return None


# ── Grupo-scoped endpoints ──────────────────────────────────────────────────

class ConceptoListCreateView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id):
        conceptos = Concepto.objects.filter(grupo_id=group_id, activo=True)
        tipo = request.query_params.get('tipo')
        if tipo:
            conceptos = conceptos.filter(tipo=tipo)
        return Response(ConceptoSerializer(conceptos, many=True).data)

    def post(self, request, group_id):
        grupo = _get_grupo_or_404(group_id)
        if not grupo:
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ConceptoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(grupo=grupo, usuario=None)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConceptoDetailView(APIView):
    permission_classes = [IsGroupMember]

    def put(self, request, group_id, concept_id):
        try:
            concepto = Concepto.objects.get(id=concept_id, grupo_id=group_id, activo=True)
        except Concepto.DoesNotExist:
            return Response({'detail': 'Concepto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ConceptoSerializer(concepto, data={'nombre': request.data.get('nombre', concepto.nombre), 'tipo': concepto.tipo})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, group_id, concept_id):
        try:
            concepto = Concepto.objects.get(id=concept_id, grupo_id=group_id, activo=True)
        except Concepto.DoesNotExist:
            return Response({'detail': 'Concepto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        has_movements = Movimiento.objects.filter(concepto=concepto).exists()
        if has_movements:
            return Response(
                {'detail': 'Este concepto tiene movimientos asociados.', 'tiene_movimientos': True, 'concepto_id': str(concepto.id)},
                status=status.HTTP_409_CONFLICT,
            )
        concepto.activo = False
        concepto.save()
        return Response({'detail': 'Concepto eliminado.'})


class ConceptoDeleteWithMovementsView(APIView):
    permission_classes = [IsGroupMember]

    def post(self, request, group_id, concept_id):
        accion = request.data.get('accion')
        if accion not in ('eliminar_movimientos', 'mantener_movimientos'):
            return Response({'detail': 'Acción inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            concepto = Concepto.objects.get(id=concept_id, grupo_id=group_id, activo=True)
        except Concepto.DoesNotExist:
            return Response({'detail': 'Concepto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if accion == 'eliminar_movimientos':
            Movimiento.objects.filter(concepto=concepto).delete()
        else:
            Movimiento.objects.filter(concepto=concepto).update(concepto=None)
        concepto.activo = False
        concepto.save()
        return Response({'detail': 'Concepto eliminado.'})


class MovimientoListView(APIView):
    """Lee movimientos de un grupo. POST bloqueado: usar /personal/movements/<id>/replicate/."""
    permission_classes = [IsGroupMember]

    def get(self, request, group_id):
        movimientos = (
            Movimiento.objects
            .filter(grupo_id=group_id)
            .select_related('concepto', 'usuario')
            .order_by('-fecha_hora')
        )
        concepto_id = request.query_params.get('concepto')
        if concepto_id:
            movimientos = movimientos.filter(concepto_id=concepto_id)
        paginator = PageNumberPagination()
        paginator.page_size = 15
        page = paginator.paginate_queryset(movimientos, request)
        return paginator.get_paginated_response(MovimientoSerializer(page, many=True).data)

    def post(self, request, group_id):
        return Response(
            {'detail': 'Los movimientos grupales solo pueden crearse mediante replicación de un movimiento personal.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class MovimientoDetailView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id, movement_id):
        try:
            movimiento = Movimiento.objects.select_related('concepto', 'usuario').get(
                id=movement_id, grupo_id=group_id
            )
        except Movimiento.DoesNotExist:
            return Response({'detail': 'Movimiento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MovimientoSerializer(movimiento).data)


class MovimientoExportView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id):
        movimientos = (
            Movimiento.objects.filter(grupo_id=group_id)
            .select_related('concepto', 'usuario')
            .order_by('-fecha_hora')
        )
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['Tipo', 'Concepto', 'Nombre', 'Detalle', 'Monto', 'Usuario', 'Fecha y hora'])
        for m in movimientos:
            concepto_nombre = m.concepto.nombre if m.concepto and m.concepto.activo else 'Desconocido'
            writer.writerow([m.tipo, concepto_nombre, m.nombre, m.detalle, m.monto,
                             m.usuario.username, m.fecha_hora.strftime('%d/%m/%Y %H:%M')])
        content = '﻿' + output.getvalue()
        response = HttpResponse(content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="movimientos_grupo.csv"'
        return response


class FinanciasDashboardView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id):
        hoy = date.today()
        mes_inicio = hoy.replace(day=1)
        movimientos_mes = Movimiento.objects.filter(
            grupo_id=group_id, fecha_hora__date__gte=mes_inicio, fecha_hora__date__lte=hoy,
        )
        gasto_mensual = movimientos_mes.filter(tipo='Gasto').aggregate(total=Sum('monto'))['total'] or 0
        ingreso_mensual = movimientos_mes.filter(tipo='Ingreso').aggregate(total=Sum('monto'))['total'] or 0
        saldo_restante = ingreso_mensual - gasto_mensual
        presupuesto_hasta_hoy = (
            RegistroPresupuesto.objects
            .filter(grupo_id=group_id, tipo='Gasto', fecha__lte=hoy)
            .aggregate(total=Sum('monto'))['total'] or 0
        )
        desviacion_presupuesto = presupuesto_hasta_hoy - gasto_mensual
        gastos_por_concepto = (
            movimientos_mes.filter(tipo='Gasto')
            .values('concepto__nombre')
            .annotate(total=Sum('monto'))
            .order_by('-total')
        )
        grafico = []
        items = list(gastos_por_concepto)
        if len(items) <= 5:
            for item in items:
                grafico.append({'concepto': item['concepto__nombre'] or 'Desconocido', 'total': item['total']})
        else:
            for item in items[:5]:
                grafico.append({'concepto': item['concepto__nombre'] or 'Desconocido', 'total': item['total']})
            otros_total = sum(item['total'] for item in items[5:])
            if otros_total > 0:
                grafico.append({'concepto': 'Otros', 'total': otros_total})
        ultimos = (
            Movimiento.objects.filter(grupo_id=group_id)
            .select_related('concepto', 'usuario')
            .order_by('-fecha_hora')[:5]
        )
        return Response({
            'gasto_acumulado_mensual': gasto_mensual,
            'saldo_restante': saldo_restante,
            'desviacion_presupuesto': desviacion_presupuesto,
            'grafico_torta': grafico,
            'ultimos_movimientos': MovimientoSerializer(ultimos, many=True).data,
        })


class PresupuestoListCreateView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id):
        registros = (
            RegistroPresupuesto.objects
            .filter(grupo_id=group_id)
            .select_related('concepto')
            .order_by('tipo', 'concepto__nombre')
        )
        total = registros.aggregate(total=Sum('monto'))['total'] or 0
        return Response({'registros': RegistroPresupuestoSerializer(registros, many=True).data, 'total': total})

    def post(self, request, group_id):
        grupo = _get_grupo_or_404(group_id)
        if not grupo:
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RegistroPresupuestoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        concepto = serializer.validated_data.get('concepto')
        if concepto and str(concepto.grupo_id) != str(group_id):
            return Response({'detail': 'El concepto no pertenece a este grupo.'}, status=status.HTTP_400_BAD_REQUEST)
        registro = serializer.save(grupo=grupo, usuario=None)
        crear_notificaciones_grupo(
            grupo, Notificacion.TIPO_PRESUPUESTO,
            f'Se realizó un cambio en el presupuesto de {registro.concepto.nombre}',
            referencia_id=registro.id, excluir_usuario=request.user,
        )
        return Response(RegistroPresupuestoSerializer(registro).data, status=status.HTTP_201_CREATED)


class PresupuestoDetailView(APIView):
    permission_classes = [IsGroupMember]

    def patch(self, request, group_id, budget_id):
        try:
            registro = RegistroPresupuesto.objects.select_related('concepto').get(id=budget_id, grupo_id=group_id)
        except RegistroPresupuesto.DoesNotExist:
            return Response({'detail': 'Registro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RegistroPresupuestoUpdateSerializer(registro, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        registro = serializer.save()
        grupo = Grupo.objects.get(id=group_id)
        crear_notificaciones_grupo(
            grupo, Notificacion.TIPO_PRESUPUESTO,
            f'Se realizó un cambio en el presupuesto de {registro.concepto.nombre}',
            referencia_id=registro.id, excluir_usuario=request.user,
        )
        return Response(RegistroPresupuestoSerializer(registro).data)

    def delete(self, request, group_id, budget_id):
        try:
            registro = RegistroPresupuesto.objects.select_related('concepto').get(id=budget_id, grupo_id=group_id)
        except RegistroPresupuesto.DoesNotExist:
            return Response({'detail': 'Registro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        nombre_concepto = registro.concepto.nombre
        grupo = Grupo.objects.get(id=group_id)
        registro.delete()
        crear_notificaciones_grupo(
            grupo, Notificacion.TIPO_PRESUPUESTO,
            f'Se realizó un cambio en el presupuesto de {nombre_concepto}',
            excluir_usuario=request.user,
        )
        return Response({'detail': 'Registro de presupuesto eliminado.'})


# ── Personal endpoints ──────────────────────────────────────────────────────

class MovimientoPersonalListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        movimientos = (
            Movimiento.objects
            .filter(usuario=request.user, grupo__isnull=True)
            .select_related('concepto')
            .order_by('-fecha_hora')
        )
        concepto_id = request.query_params.get('concepto')
        if concepto_id:
            movimientos = movimientos.filter(concepto_id=concepto_id)
        paginator = PageNumberPagination()
        paginator.page_size = 15
        page = paginator.paginate_queryset(movimientos, request)
        return paginator.get_paginated_response(MovimientoSerializer(page, many=True).data)

    def post(self, request):
        serializer = MovimientoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        concepto = serializer.validated_data.get('concepto')
        if concepto and concepto.usuario_id != request.user.pk:
            return Response({'detail': 'El concepto no pertenece al usuario.'}, status=status.HTTP_400_BAD_REQUEST)
        movimiento = serializer.save(usuario=request.user, grupo=None)
        return Response(MovimientoSerializer(movimiento).data, status=status.HTTP_201_CREATED)


class MovimientoPersonalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movement_id):
        try:
            movimiento = Movimiento.objects.select_related('concepto').get(
                id=movement_id, usuario=request.user, grupo__isnull=True
            )
        except Movimiento.DoesNotExist:
            return Response({'detail': 'Movimiento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        replicas = ReplicaGrupal.objects.filter(movimiento_personal=movimiento).select_related('grupo')
        data = MovimientoSerializer(movimiento).data
        data['replicas'] = ReplicaGrupalSerializer(replicas, many=True).data
        return Response(data)


class ReplicarMovimientoView(APIView):
    """Replica un movimiento personal a un grupo."""
    permission_classes = [IsAuthenticated]

    def post(self, request, movement_id):
        try:
            mov_personal = Movimiento.objects.get(id=movement_id, usuario=request.user, grupo__isnull=True)
        except Movimiento.DoesNotExist:
            return Response({'detail': 'Movimiento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        grupo_id = request.data.get('grupo_id')
        es_compartido = request.data.get('es_compartido', False)
        usuario_deudor_id = request.data.get('usuario_deudor_id')

        if not grupo_id:
            return Response({'detail': 'grupo_id es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        if not GrupoMiembro.objects.filter(usuario=request.user, grupo_id=grupo_id, grupo__activo=True).exists():
            return Response({'detail': 'No eres miembro de este grupo.'}, status=status.HTTP_403_FORBIDDEN)

        if ReplicaGrupal.objects.filter(movimiento_personal=mov_personal, grupo_id=grupo_id).exists():
            return Response({'detail': 'Este movimiento ya fue replicado a este grupo.'}, status=status.HTTP_409_CONFLICT)

        try:
            grupo = Grupo.objects.get(id=grupo_id, activo=True)
        except Grupo.DoesNotExist:
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        concepto_grupal = None
        if mov_personal.concepto:
            concepto_grupal = Concepto.objects.filter(
                grupo=grupo, nombre=mov_personal.concepto.nombre,
                tipo=mov_personal.concepto.tipo, activo=True,
            ).first()

        mov_grupo = Movimiento.objects.create(
            tipo=mov_personal.tipo, nombre=mov_personal.nombre,
            detalle=mov_personal.detalle, monto=mov_personal.monto,
            concepto=concepto_grupal, usuario=request.user,
            grupo=grupo, fecha_hora=mov_personal.fecha_hora,
        )
        replica = ReplicaGrupal.objects.create(
            movimiento_personal=mov_personal, movimiento_grupo=mov_grupo, grupo=grupo
        )

        tipo_notif = Notificacion.TIPO_GASTO if mov_personal.tipo == 'Gasto' else Notificacion.TIPO_INGRESO
        concepto_nombre = concepto_grupal.nombre if concepto_grupal else 'sin concepto'
        titulo = (
            f'Se {"generó un gasto" if mov_personal.tipo == "Gasto" else "registró un ingreso"} '
            f'por ${mov_personal.monto:,} de {request.user.username} por {concepto_nombre}'
        ).replace(',', '.')
        crear_notificaciones_grupo(grupo, tipo_notif, titulo, referencia_id=mov_grupo.id, excluir_usuario=request.user)

        gasto_compartido_data = None
        if es_compartido and mov_personal.tipo == 'Gasto' and usuario_deudor_id:
            try:
                miembro = GrupoMiembro.objects.select_related('usuario').get(usuario_id=usuario_deudor_id, grupo=grupo)
                gc = GastoCompartido.objects.create(
                    movimiento=mov_grupo,
                    usuario_acreedor=request.user,
                    usuario_deudor=miembro.usuario,
                    monto_pendiente=mov_grupo.monto,
                    grupo=grupo,
                )
                Notificacion.objects.create(
                    titulo=f'{request.user.username} te compartió un gasto de ${gc.monto_pendiente:,} por {concepto_nombre}.'.replace(',', '.'),
                    tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                    referencia_id=mov_grupo.id,
                    usuario=miembro.usuario,
                )
                gasto_compartido_data = {'id': str(gc.id), 'monto_pendiente': gc.monto_pendiente}
            except GrupoMiembro.DoesNotExist:
                pass

        return Response({
            'replica': ReplicaGrupalSerializer(replica).data,
            'gasto_compartido': gasto_compartido_data,
        }, status=status.HTTP_201_CREATED)


class FinanciasDashboardPersonalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoy = date.today()
        mes_inicio = hoy.replace(day=1)
        movimientos_mes = Movimiento.objects.filter(
            usuario=request.user, grupo__isnull=True,
            fecha_hora__date__gte=mes_inicio, fecha_hora__date__lte=hoy,
        )
        gasto_mensual = movimientos_mes.filter(tipo='Gasto').aggregate(total=Sum('monto'))['total'] or 0
        ingreso_mensual = movimientos_mes.filter(tipo='Ingreso').aggregate(total=Sum('monto'))['total'] or 0
        saldo_restante = ingreso_mensual - gasto_mensual
        presupuesto_hasta_hoy = (
            RegistroPresupuesto.objects
            .filter(usuario=request.user, grupo__isnull=True, tipo='Gasto', fecha__lte=hoy)
            .aggregate(total=Sum('monto'))['total'] or 0
        )
        desviacion_presupuesto = presupuesto_hasta_hoy - gasto_mensual
        gastos_por_concepto = (
            movimientos_mes.filter(tipo='Gasto')
            .values('concepto__nombre')
            .annotate(total=Sum('monto'))
            .order_by('-total')
        )
        grafico = []
        items = list(gastos_por_concepto)
        if len(items) <= 5:
            for item in items:
                grafico.append({'concepto': item['concepto__nombre'] or 'Desconocido', 'total': item['total']})
        else:
            for item in items[:5]:
                grafico.append({'concepto': item['concepto__nombre'] or 'Desconocido', 'total': item['total']})
            otros_total = sum(item['total'] for item in items[5:])
            if otros_total > 0:
                grafico.append({'concepto': 'Otros', 'total': otros_total})
        ultimos = (
            Movimiento.objects.filter(usuario=request.user, grupo__isnull=True)
            .select_related('concepto')
            .order_by('-fecha_hora')[:5]
        )
        return Response({
            'gasto_acumulado_mensual': gasto_mensual,
            'saldo_restante': saldo_restante,
            'desviacion_presupuesto': desviacion_presupuesto,
            'grafico_torta': grafico,
            'ultimos_movimientos': MovimientoSerializer(ultimos, many=True).data,
        })
