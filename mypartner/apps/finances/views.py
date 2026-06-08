import csv
import io
import logging
from datetime import date

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.groups.models import Grupo, GrupoMiembro
from apps.groups.permissions import IsGroupAdmin, IsGroupMember
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from .models import (
    AporteAhorro, Concepto, DivisionPresupuesto, GastoCompartido,
    MetaAhorro, Movimiento, RegistroPresupuesto, ReplicaGrupal, Tarjeta,
)
from .serializers import (
    AporteAhorroSerializer,
    ConceptoSerializer,
    GastoCompartidoSerializer,
    MetaAhorroCreateSerializer,
    MetaAhorroSerializer,
    MovimientoCreateSerializer,
    MovimientoSerializer,
    PresupuestoPersonalCreateSerializer,
    RegistroPresupuestoSerializer,
    RegistroPresupuestoUpdateSerializer,
    ReplicaGrupalSerializer,
    SplitConfirmInputSerializer,
    TarjetaCreateSerializer,
    TarjetaSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_grupo_or_404(group_id):
    try:
        return Grupo.objects.get(id=group_id, activo=True)
    except Grupo.DoesNotExist:
        logger.warning('Grupo %s no encontrado o inactivo.', group_id)
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
        concepto = serializer.save(grupo=grupo, usuario=None)
        logger.info('Concepto creado grupo=%s nombre=%s user=%s', group_id, concepto.nombre, request.user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConceptoDetailView(APIView):
    permission_classes = [IsGroupMember]

    def put(self, request, group_id, concept_id):
        try:
            concepto = Concepto.objects.get(id=concept_id, grupo_id=group_id, activo=True)
        except Concepto.DoesNotExist:
            logger.warning('Concepto %s no encontrado grupo=%s user=%s', concept_id, group_id, request.user.id)
            return Response({'detail': 'Concepto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ConceptoSerializer(concepto, data={'nombre': request.data.get('nombre', concepto.nombre), 'tipo': concepto.tipo})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info('Concepto actualizado grupo=%s id=%s user=%s', group_id, concept_id, request.user.id)
        return Response(serializer.data)

    def delete(self, request, group_id, concept_id):
        try:
            concepto = Concepto.objects.get(id=concept_id, grupo_id=group_id, activo=True)
        except Concepto.DoesNotExist:
            logger.warning('Concepto %s no encontrado grupo=%s user=%s', concept_id, group_id, request.user.id)
            return Response({'detail': 'Concepto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        has_movements = Movimiento.objects.filter(concepto=concepto).exists()
        if has_movements:
            logger.warning('Concepto %s tiene movimientos, no se puede eliminar grupo=%s user=%s', concept_id, group_id, request.user.id)
            return Response(
                {'detail': 'Este concepto tiene movimientos asociados.', 'tiene_movimientos': True, 'concepto_id': str(concepto.id)},
                status=status.HTTP_409_CONFLICT,
            )
        concepto.activo = False
        concepto.save()
        logger.info('Concepto eliminado grupo=%s id=%s user=%s', group_id, concept_id, request.user.id)
        return Response({'detail': 'Concepto eliminado.'})


class ConceptoDeleteWithMovementsView(APIView):
    permission_classes = [IsGroupMember]

    def post(self, request, group_id, concept_id):
        accion = request.data.get('accion')
        if accion not in ('eliminar_movimientos', 'mantener_movimientos'):
            logger.warning('Acción inválida "%s" en ConceptoDeleteWithMovements grupo=%s user=%s', accion, group_id, request.user.id)
            return Response({'detail': 'Acción inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            concepto = Concepto.objects.get(id=concept_id, grupo_id=group_id, activo=True)
        except Concepto.DoesNotExist:
            logger.warning('Concepto %s no encontrado grupo=%s user=%s', concept_id, group_id, request.user.id)
            return Response({'detail': 'Concepto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if accion == 'eliminar_movimientos':
            deleted_count = Movimiento.objects.filter(concepto=concepto).delete()[0]
            logger.info('Concepto %s eliminado con %d movimientos grupo=%s user=%s', concept_id, deleted_count, group_id, request.user.id)
        else:
            Movimiento.objects.filter(concepto=concepto).update(concepto=None)
            logger.info('Concepto %s eliminado, movimientos conservados grupo=%s user=%s', concept_id, group_id, request.user.id)
        concepto.activo = False
        concepto.save()
        return Response({'detail': 'Concepto eliminado.'})


class MovimientoListView(APIView):
    """Lee movimientos de un grupo. POST bloqueado: usar /personal/movements/<id>/replicate/."""
    permission_classes = [IsGroupMember]

    def get(self, request, group_id):
        concepto_id = request.query_params.get('concepto')
        logger.debug('Listando movimientos grupo=%s concepto=%s user=%s', group_id, concepto_id, request.user.id)
        movimientos = (
            Movimiento.objects
            .filter(grupo_id=group_id)
            .select_related('concepto', 'usuario')
            .order_by('-fecha_hora')
        )
        if concepto_id:
            movimientos = movimientos.filter(concepto_id=concepto_id)
        paginator = PageNumberPagination()
        paginator.page_size = 15
        page = paginator.paginate_queryset(movimientos, request)
        return paginator.get_paginated_response(MovimientoSerializer(page, many=True).data)

    def post(self, request, group_id):
        logger.debug('POST bloqueado en MovimientoListView grupo=%s user=%s', group_id, request.user.id)
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
        logger.info('Exportando movimientos CSV grupo=%s user=%s', group_id, request.user.id)
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
        logger.debug('Creando registro presupuesto grupo=%s data=%s user=%s', group_id, request.data, request.user.id)
        grupo = _get_grupo_or_404(group_id)
        if not grupo:
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RegistroPresupuestoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        concepto = serializer.validated_data.get('concepto')
        if concepto and str(concepto.grupo_id) != str(group_id):
            logger.warning('Concepto %s no pertenece al grupo=%s user=%s', concepto.id, group_id, request.user.id)
            return Response({'detail': 'El concepto no pertenece a este grupo.'}, status=status.HTTP_400_BAD_REQUEST)
        registro = serializer.save(grupo=grupo, usuario=None)
        logger.info('RegistroPresupuesto creado grupo=%s id=%s concepto=%s user=%s', group_id, registro.id, registro.concepto.nombre, request.user.id)
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
            logger.warning('RegistroPresupuesto %s no encontrado grupo=%s user=%s', budget_id, group_id, request.user.id)
            return Response({'detail': 'Registro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RegistroPresupuestoUpdateSerializer(registro, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        registro = serializer.save()
        logger.info('RegistroPresupuesto actualizado grupo=%s id=%s user=%s', group_id, budget_id, request.user.id)
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
            logger.warning('RegistroPresupuesto %s no encontrado grupo=%s user=%s', budget_id, group_id, request.user.id)
            return Response({'detail': 'Registro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        nombre_concepto = registro.concepto.nombre
        grupo = Grupo.objects.get(id=group_id)
        registro.delete()
        logger.info('RegistroPresupuesto eliminado grupo=%s id=%s concepto=%s user=%s', group_id, budget_id, nombre_concepto, request.user.id)
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
            .select_related('concepto', 'tarjeta')
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
        logger.debug(
            'Creando movimiento personal user=%s tipo=%s monto=%s concepto=%s grupo=%s compartido=%s',
            request.user.id,
            request.data.get('tipo'),
            request.data.get('monto'),
            request.data.get('concepto'),
            request.data.get('grupo_id'),
            request.data.get('es_compartido'),
        )
        serializer = MovimientoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        concepto = serializer.validated_data.get('concepto')
        if concepto and concepto.usuario_id != request.user.pk:
            logger.warning('Concepto %s no pertenece al user=%s', concepto.id, request.user.id)
            return Response({'detail': 'El concepto no pertenece al usuario.'}, status=status.HTTP_400_BAD_REQUEST)

        tarjeta = serializer.validated_data.get('tarjeta')
        if tarjeta and tarjeta.usuario_id != request.user.pk:
            logger.warning('Tarjeta %s no pertenece al user=%s', tarjeta.id, request.user.id)
            return Response({'detail': 'La tarjeta no pertenece al usuario.'}, status=status.HTTP_400_BAD_REQUEST)

        # Campos opcionales de replicación (no pasan por el serializer del modelo)
        registrar_en_grupo = bool(request.data.get('registrar_en_grupo', False))
        grupo_id = request.data.get('grupo_id')
        es_compartido = bool(request.data.get('es_compartido', False))
        usuario_deudor_id = request.data.get('usuario_deudor_id')
        monto_compartido_raw = request.data.get('monto_compartido')

        grupo = None
        if registrar_en_grupo and grupo_id:
            if not GrupoMiembro.objects.filter(
                usuario=request.user, grupo_id=grupo_id, grupo__activo=True
            ).exists():
                return Response({'detail': 'No eres miembro del grupo seleccionado.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                grupo = Grupo.objects.get(id=grupo_id, activo=True)
            except Grupo.DoesNotExist:
                return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            mov_personal = serializer.save(usuario=request.user, grupo=None)

            if tarjeta and tarjeta.tipo == Tarjeta.TIPO_CREDITO and mov_personal.tipo == Movimiento.TIPO_GASTO:
                tarjeta.cupo_usado = (tarjeta.cupo_usado or 0) + mov_personal.monto
                tarjeta.save(update_fields=['cupo_usado'])

            replica_data = None
            gasto_compartido_data = None

            if grupo:
                concepto_grupal = None
                if concepto:
                    concepto_grupal, _ = Concepto.objects.get_or_create(
                        grupo=grupo, nombre=concepto.nombre, tipo=concepto.tipo,
                        defaults={'activo': True, 'usuario': None},
                    )
                mov_grupo = Movimiento.objects.create(
                    tipo=mov_personal.tipo, nombre=mov_personal.nombre,
                    detalle=mov_personal.detalle, monto=mov_personal.monto,
                    concepto=concepto_grupal, usuario=request.user,
                    grupo=grupo, fecha_hora=mov_personal.fecha_hora,
                )
                replica = ReplicaGrupal.objects.create(
                    movimiento_personal=mov_personal,
                    movimiento_grupo=mov_grupo,
                    grupo=grupo,
                )
                tipo_notif = Notificacion.TIPO_GASTO if mov_personal.tipo == 'Gasto' else Notificacion.TIPO_INGRESO
                concepto_nombre = concepto_grupal.nombre if concepto_grupal else 'sin concepto'
                titulo = (
                    f'Se {"generó un gasto" if mov_personal.tipo == "Gasto" else "registró un ingreso"} '
                    f'por ${mov_personal.monto:,} de {request.user.username} por {concepto_nombre}'
                ).replace(',', '.')
                crear_notificaciones_grupo(grupo, tipo_notif, titulo, referencia_id=mov_grupo.id, excluir_usuario=request.user)
                replica_data = ReplicaGrupalSerializer(replica).data

                if es_compartido and mov_personal.tipo == 'Gasto' and usuario_deudor_id:
                    try:
                        monto_pendiente = int(monto_compartido_raw) if monto_compartido_raw else mov_personal.monto
                        monto_pendiente = max(1, min(monto_pendiente, mov_personal.monto - 1))
                        miembro = GrupoMiembro.objects.select_related('usuario').get(
                            usuario_id=usuario_deudor_id, grupo=grupo
                        )
                        gc = GastoCompartido.objects.create(
                            movimiento=mov_grupo,
                            usuario_acreedor=request.user,
                            usuario_deudor=miembro.usuario,
                            monto_pendiente=monto_pendiente,
                            grupo=grupo,
                        )
                        Notificacion.objects.create(
                            titulo=f'{request.user.username} te compartió un gasto de ${monto_pendiente:,} por {concepto_nombre}.'.replace(',', '.'),
                            tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                            referencia_id=mov_grupo.id,
                            usuario=miembro.usuario,
                        )
                        gasto_compartido_data = {'id': str(gc.id), 'monto_pendiente': gc.monto_pendiente}
                    except GrupoMiembro.DoesNotExist:
                        pass

        logger.info(
            'Movimiento personal creado id=%s tipo=%s monto=%s user=%s replica_grupo=%s gasto_compartido=%s',
            mov_personal.id, mov_personal.tipo, mov_personal.monto, request.user.id,
            replica_data is not None, gasto_compartido_data is not None,
        )
        response_data = MovimientoSerializer(mov_personal).data
        response_data['replica'] = replica_data
        response_data['gasto_compartido'] = gasto_compartido_data
        return Response(response_data, status=status.HTTP_201_CREATED)


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
        logger.debug('Replicando movimiento %s a grupo=%s user=%s', movement_id, request.data.get('grupo_id'), request.user.id)
        try:
            mov_personal = Movimiento.objects.get(id=movement_id, usuario=request.user, grupo__isnull=True)
        except Movimiento.DoesNotExist:
            logger.warning('Movimiento %s no encontrado para replicar user=%s', movement_id, request.user.id)
            return Response({'detail': 'Movimiento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        grupo_id = request.data.get('grupo_id')
        es_compartido = request.data.get('es_compartido', False)
        usuario_deudor_id = request.data.get('usuario_deudor_id')

        if not grupo_id:
            return Response({'detail': 'grupo_id es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        if not GrupoMiembro.objects.filter(usuario=request.user, grupo_id=grupo_id, grupo__activo=True).exists():
            logger.warning('User=%s no es miembro del grupo=%s para replicar movimiento', request.user.id, grupo_id)
            return Response({'detail': 'No eres miembro de este grupo.'}, status=status.HTTP_403_FORBIDDEN)

        if ReplicaGrupal.objects.filter(movimiento_personal=mov_personal, grupo_id=grupo_id).exists():
            logger.warning('Movimiento %s ya replicado al grupo=%s user=%s', movement_id, grupo_id, request.user.id)
            return Response({'detail': 'Este movimiento ya fue replicado a este grupo.'}, status=status.HTTP_409_CONFLICT)

        try:
            grupo = Grupo.objects.get(id=grupo_id, activo=True)
        except Grupo.DoesNotExist:
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        concepto_grupal = None
        if mov_personal.concepto:
            concepto_grupal, _ = Concepto.objects.get_or_create(
                grupo=grupo, nombre=mov_personal.concepto.nombre,
                tipo=mov_personal.concepto.tipo,
                defaults={'activo': True, 'usuario': None},
            )

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

        logger.info(
            'Movimiento %s replicado a grupo=%s user=%s gasto_compartido=%s',
            movement_id, grupo_id, request.user.id, gasto_compartido_data is not None,
        )
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


# ── Conceptos personales ────────────────────────────────────────────────────

class ConceptoPersonalListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conceptos = Concepto.objects.filter(
            usuario=request.user, grupo__isnull=True, activo=True
        ).order_by('tipo', 'nombre')
        tipo = request.query_params.get('tipo')
        if tipo:
            conceptos = conceptos.filter(tipo=tipo)
        return Response(ConceptoSerializer(conceptos, many=True).data)

    def post(self, request):
        serializer = ConceptoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nombre = serializer.validated_data['nombre']
        if Concepto.objects.filter(usuario=request.user, nombre__iexact=nombre, activo=True, grupo__isnull=True).exists():
            logger.warning('Concepto duplicado "%s" user=%s', nombre, request.user.id)
            return Response({'detail': f'Ya existe un concepto llamado "{nombre}".'}, status=status.HTTP_409_CONFLICT)
        concepto = serializer.save(usuario=request.user, grupo=None)
        logger.info('Concepto personal creado id=%s nombre=%s user=%s', concepto.id, concepto.nombre, request.user.id)
        return Response(ConceptoSerializer(concepto).data, status=status.HTTP_201_CREATED)


class ConceptoPersonalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, concept_id):
        try:
            concepto = Concepto.objects.get(id=concept_id, usuario=request.user, activo=True, grupo__isnull=True)
        except Concepto.DoesNotExist:
            logger.warning('Concepto personal %s no encontrado user=%s', concept_id, request.user.id)
            return Response({'detail': 'Concepto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        nombre = request.data.get('nombre', concepto.nombre).strip()
        if Concepto.objects.filter(
            usuario=request.user, nombre__iexact=nombre, activo=True, grupo__isnull=True
        ).exclude(id=concept_id).exists():
            logger.warning('Concepto duplicado "%s" user=%s', nombre, request.user.id)
            return Response({'detail': f'Ya existe un concepto llamado "{nombre}".'}, status=status.HTTP_409_CONFLICT)
        serializer = ConceptoSerializer(concepto, data={'nombre': nombre, 'tipo': concepto.tipo})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info('Concepto personal actualizado id=%s nombre=%s user=%s', concept_id, nombre, request.user.id)
        return Response(serializer.data)

    def delete(self, request, concept_id):
        try:
            concepto = Concepto.objects.get(id=concept_id, usuario=request.user, activo=True, grupo__isnull=True)
        except Concepto.DoesNotExist:
            logger.warning('Concepto personal %s no encontrado user=%s', concept_id, request.user.id)
            return Response({'detail': 'Concepto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if Movimiento.objects.filter(concepto=concepto).exists():
            logger.warning('Concepto personal %s tiene movimientos, no se puede eliminar user=%s', concept_id, request.user.id)
            return Response(
                {'detail': 'Este concepto tiene movimientos asociados.', 'tiene_movimientos': True, 'concepto_id': str(concepto.id)},
                status=status.HTTP_409_CONFLICT,
            )
        concepto.activo = False
        concepto.save()
        logger.info('Concepto personal eliminado id=%s user=%s', concept_id, request.user.id)
        return Response({'detail': 'Concepto eliminado.'})


class ConceptoPersonalDeleteWithMovementsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, concept_id):
        accion = request.data.get('accion')
        if accion not in ('eliminar_movimientos', 'mantener_movimientos'):
            logger.warning('Acción inválida "%s" en ConceptoPersonalDeleteWithMovements id=%s user=%s', accion, concept_id, request.user.id)
            return Response({'detail': 'Acción inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            concepto = Concepto.objects.get(id=concept_id, usuario=request.user, activo=True, grupo__isnull=True)
        except Concepto.DoesNotExist:
            logger.warning('Concepto personal %s no encontrado user=%s', concept_id, request.user.id)
            return Response({'detail': 'Concepto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if accion == 'eliminar_movimientos':
            deleted_count = Movimiento.objects.filter(concepto=concepto).delete()[0]
            logger.info('Concepto personal %s eliminado con %d movimientos user=%s', concept_id, deleted_count, request.user.id)
        else:
            Movimiento.objects.filter(concepto=concepto).update(concepto=None)
            logger.info('Concepto personal %s eliminado, movimientos conservados user=%s', concept_id, request.user.id)
        concepto.activo = False
        concepto.save()
        return Response({'detail': 'Concepto eliminado.'})


# ── Corrección de movimiento personal ──────────────────────────────────────

class MovimientoPersonalCorrectView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, movement_id):
        logger.debug('Corrigiendo movimiento %s monto_final=%s user=%s', movement_id, request.data.get('monto_final'), request.user.id)
        try:
            mov = Movimiento.objects.get(
                id=movement_id, usuario=request.user,
                grupo__isnull=True, tipo=Movimiento.TIPO_GASTO,
            )
        except Movimiento.DoesNotExist:
            logger.warning('Movimiento %s no encontrado para corrección user=%s', movement_id, request.user.id)
            return Response({'detail': 'Movimiento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        monto_final_raw = str(request.data.get('monto_final', '0')).replace('.', '').replace(',', '')
        try:
            monto_final = int(monto_final_raw)
            assert monto_final > 0
        except (ValueError, AssertionError):
            logger.warning('Monto inválido "%s" en corrección movimiento=%s user=%s', monto_final_raw, movement_id, request.user.id)
            return Response({'detail': 'Monto inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        diferencia = monto_final - mov.monto
        if diferencia == 0:
            return Response({'detail': 'El monto es igual al original.'}, status=status.HTTP_400_BAD_REQUEST)

        tipo_correccion = Movimiento.TIPO_GASTO if diferencia > 0 else Movimiento.TIPO_INGRESO
        monto_correccion = abs(diferencia)
        monto_original = mov.monto

        with transaction.atomic():
            correccion = Movimiento.objects.create(
                tipo=tipo_correccion,
                nombre='Corrección de gasto',
                detalle=f'Corrección de «{mov.nombre}»: ${monto_original:,} → ${monto_final:,}'.replace(',', '.'),
                monto=monto_correccion,
                concepto=None,
                usuario=request.user,
                grupo=None,
                fecha_hora=timezone.now(),
            )
            replicas = ReplicaGrupal.objects.filter(movimiento_personal=mov).select_related('movimiento_grupo')
            for replica in replicas:
                mov_grupo = replica.movimiento_grupo
                compartidos = GastoCompartido.objects.filter(movimiento=mov_grupo, pagado=False).select_related('usuario_deudor')
                for gc in compartidos:
                    monto_anterior = gc.monto_pendiente
                    nuevo_monto = max(1, round(monto_anterior * monto_final / monto_original))
                    gc.monto_pendiente = nuevo_monto
                    gc.save()
                    Notificacion.objects.create(
                        titulo=(
                            f'{request.user.username} corrigió el gasto «{mov.nombre}»: '
                            f'tu deuda cambió de ${monto_anterior:,} a ${nuevo_monto:,}.'
                        ).replace(',', '.'),
                        tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                        referencia_id=mov_grupo.id,
                        usuario=gc.usuario_deudor,
                    )
                mov_grupo.monto = monto_final
                mov_grupo.save()

        logger.info(
            'Corrección registrada movimiento=%s original=%s final=%s diferencia=%s user=%s',
            movement_id, mov.monto, monto_final, diferencia, request.user.id,
        )
        signo = '+' if diferencia > 0 else '-'
        return Response({
            'detail': f'Corrección registrada: {signo}${monto_correccion:,} como {tipo_correccion.lower()}.'.replace(',', '.'),
            'correccion': MovimientoSerializer(correccion).data,
        })


# ── Presupuesto personal ────────────────────────────────────────────────────

class PresupuestoPersonalListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoy = date.today()
        mes_raw = request.query_params.get('mes', hoy.strftime('%Y-%m'))
        try:
            anio_str, mes_str = mes_raw.split('-')
            anio, mes = int(anio_str), int(mes_str)
        except (ValueError, AttributeError):
            anio, mes = hoy.year, hoy.month

        base_qs = (
            RegistroPresupuesto.objects
            .filter(usuario=request.user, grupo__isnull=True)
            .filter(
                Q(periodicidad='Mensual', fecha__year__lt=anio) |
                Q(periodicidad='Mensual', fecha__year=anio, fecha__month__lte=mes) |
                Q(periodicidad='Anual', fecha__month=mes, fecha__year__lte=anio) |
                Q(periodicidad='Puntual', fecha__year=anio, fecha__month=mes)
            )
            .filter(
                Q(fecha_fin__isnull=True) |
                Q(fecha_fin__year__gt=anio) |
                Q(fecha_fin__year=anio, fecha_fin__month__gte=mes)
            )
            .select_related('concepto')
            .prefetch_related('divisiones__usuario')
            .order_by('-tipo', '-monto')
        )
        ingresos = base_qs.filter(tipo='Ingreso').aggregate(t=Sum('monto'))['t'] or 0
        gastos = base_qs.filter(tipo='Gasto').aggregate(t=Sum('monto'))['t'] or 0
        return Response({
            'registros': RegistroPresupuestoSerializer(base_qs, many=True).data,
            'total': ingresos - gastos,
            'total_ingresos': ingresos,
            'total_gastos': gastos,
        })

    def post(self, request):
        logger.debug(
            'Creando presupuesto personal user=%s tipo=%s monto=%s concepto=%s dividir=%s',
            request.user.id,
            request.data.get('tipo'),
            request.data.get('monto'),
            request.data.get('concepto'),
            request.data.get('dividir_presupuesto'),
        )
        serializer = PresupuestoPersonalCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        concepto = data['concepto']
        if concepto.usuario_id != request.user.pk:
            logger.warning('Concepto %s no pertenece al user=%s en presupuesto personal', concepto.id, request.user.id)
            return Response({'detail': 'El concepto no pertenece al usuario.'}, status=status.HTTP_400_BAD_REQUEST)

        dividir = data.get('dividir_presupuesto', False)
        grupo_division_id = data.get('grupo_division_id')
        divisiones_input = data.get('divisiones', [])

        campos_base = dict(
            tipo=data['tipo'],
            nombre=data['nombre'],
            fecha=data['fecha'],
            periodicidad=data.get('periodicidad', 'Puntual'),
            fecha_fin=data.get('fecha_fin'),
        )
        monto = data['monto']

        if dividir and grupo_division_id:
            if not GrupoMiembro.objects.filter(
                usuario=request.user, grupo_id=grupo_division_id, grupo__activo=True
            ).exists():
                logger.warning('User=%s no es miembro del grupo=%s para dividir presupuesto', request.user.id, grupo_division_id)
                return Response({'detail': 'No eres miembro del grupo seleccionado.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                grupo_div = Grupo.objects.get(id=grupo_division_id, activo=True)
            except Grupo.DoesNotExist:
                logger.warning('Grupo %s no encontrado para dividir presupuesto user=%s', grupo_division_id, request.user.id)
                return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

            otros_total = sum(int(d['monto']) for d in divisiones_input)
            monto_propietario = monto - otros_total
            if monto_propietario < 0:
                logger.warning('Suma de divisiones %d supera total %d en presupuesto user=%s', otros_total, monto, request.user.id)
                return Response({'detail': 'La suma de montos supera el total del presupuesto.'}, status=status.HTTP_400_BAD_REQUEST)

            usuarios_div = []
            for d in divisiones_input:
                try:
                    user_div = User.objects.get(id=d['usuario_id'])
                except User.DoesNotExist:
                    return Response({'detail': f'Usuario {d["usuario_id"]} no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
                if not GrupoMiembro.objects.filter(usuario=user_div, grupo=grupo_div, grupo__activo=True).exists():
                    return Response({'detail': f'{user_div.username} no es miembro del grupo.'}, status=status.HTTP_400_BAD_REQUEST)
                usuarios_div.append((user_div, int(d['monto'])))

            with transaction.atomic():
                detalle_ref = f'Grupo: {grupo_div.nombre} · Total: ${monto:,}'.replace(',', '.')
                detalle_texto = data.get('detalle', '')
                detalle_full = f'{detalle_ref}\n{detalle_texto}'.strip() if detalle_texto else detalle_ref

                concepto_grupo, _ = Concepto.objects.get_or_create(
                    grupo=grupo_div, nombre=concepto.nombre, tipo=data['tipo'],
                    defaults={'activo': True, 'usuario': None},
                )
                registro_grupo = RegistroPresupuesto.objects.create(
                    **campos_base, concepto=concepto_grupo,
                    detalle=detalle_full, monto=monto,
                    usuario=None, grupo=grupo_div,
                )
                RegistroPresupuesto.objects.create(
                    **campos_base, concepto=concepto,
                    detalle=detalle_full, monto=monto_propietario,
                    usuario=request.user, grupo=None,
                )
                divisiones_objs = [
                    DivisionPresupuesto(
                        registro_presupuesto=registro_grupo,
                        grupo=grupo_div, usuario=request.user,
                        monto=monto_propietario,
                    )
                ]
                for user_div, monto_div in usuarios_div:
                    concepto_div, _ = Concepto.objects.get_or_create(
                        usuario=user_div, nombre=concepto.nombre, tipo=data['tipo'],
                        defaults={'activo': True, 'grupo': None},
                    )
                    RegistroPresupuesto.objects.create(
                        **campos_base, concepto=concepto_div,
                        detalle=detalle_full, monto=monto_div,
                        usuario=user_div, grupo=None,
                    )
                    divisiones_objs.append(DivisionPresupuesto(
                        registro_presupuesto=registro_grupo,
                        grupo=grupo_div, usuario=user_div,
                        monto=monto_div,
                    ))
                    Notificacion.objects.create(
                        titulo=(
                            f'{request.user.username} te asignó '
                            f'${monto_div:,} del presupuesto "{data["nombre"]}" '
                            f'en {grupo_div.nombre}'
                        ).replace(',', '.'),
                        tipo=Notificacion.TIPO_PRESUPUESTO,
                        referencia_id=registro_grupo.id,
                        usuario=user_div,
                    )
                DivisionPresupuesto.objects.bulk_create(divisiones_objs)

            logger.info(
                'PresupuestoPersonal con división creado grupo=%s id=%s concepto=%s monto=%s user=%s divisiones=%d',
                grupo_div.id, registro_grupo.id, concepto.nombre, monto, request.user.id, len(divisiones_objs),
            )
            return Response(RegistroPresupuestoSerializer(registro_grupo).data, status=status.HTTP_201_CREATED)

        registro = RegistroPresupuesto.objects.create(
            **campos_base, concepto=concepto,
            detalle=data.get('detalle', ''), monto=monto,
            usuario=request.user, grupo=None,
        )
        logger.info('PresupuestoPersonal creado id=%s concepto=%s monto=%s user=%s', registro.id, concepto.nombre, monto, request.user.id)
        return Response(RegistroPresupuestoSerializer(registro).data, status=status.HTTP_201_CREATED)


class PresupuestoPersonalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, budget_id):
        try:
            registro = RegistroPresupuesto.objects.get(id=budget_id, usuario=request.user, grupo__isnull=True)
        except RegistroPresupuesto.DoesNotExist:
            logger.warning('PresupuestoPersonal %s no encontrado user=%s', budget_id, request.user.id)
            return Response({'detail': 'Registro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RegistroPresupuestoUpdateSerializer(registro, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info('PresupuestoPersonal actualizado id=%s user=%s', budget_id, request.user.id)
        return Response(RegistroPresupuestoSerializer(registro).data)

    def delete(self, request, budget_id):
        try:
            registro = RegistroPresupuesto.objects.get(id=budget_id, usuario=request.user, grupo__isnull=True)
        except RegistroPresupuesto.DoesNotExist:
            logger.warning('PresupuestoPersonal %s no encontrado user=%s', budget_id, request.user.id)
            return Response({'detail': 'Registro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        registro.delete()
        logger.info('PresupuestoPersonal eliminado id=%s user=%s', budget_id, request.user.id)
        return Response({'detail': 'Registro de presupuesto eliminado.'})


# ── Gastos compartidos ──────────────────────────────────────────────────────

class GastoCompartidoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        grupos_ids = (
            GrupoMiembro.objects
            .filter(usuario=request.user, grupo__activo=True)
            .values_list('grupo_id', flat=True)
        )
        pendientes_pago = list(
            GastoCompartido.objects
            .filter(usuario_deudor=request.user, grupo_id__in=grupos_ids, pagado=False)
            .select_related('movimiento__concepto', 'usuario_acreedor', 'grupo')
            .order_by('-created_at')
        )
        pendientes_cobro = list(
            GastoCompartido.objects
            .filter(usuario_acreedor=request.user, grupo_id__in=grupos_ids, pagado=False)
            .select_related('movimiento__concepto', 'usuario_deudor', 'grupo')
            .order_by('-created_at')
        )
        total_debo = sum(g.monto_pendiente for g in pendientes_pago)
        total_me_deben = sum(g.monto_pendiente for g in pendientes_cobro)

        usuarios_con_deudas: dict = {}
        for g in pendientes_pago:
            uid = str(g.usuario_acreedor_id)
            usuarios_con_deudas.setdefault(uid, {'id': uid, 'username': g.usuario_acreedor.username, 'debo': 0, 'me_deben': 0})
            usuarios_con_deudas[uid]['debo'] += g.monto_pendiente
        for g in pendientes_cobro:
            uid = str(g.usuario_deudor_id)
            usuarios_con_deudas.setdefault(uid, {'id': uid, 'username': g.usuario_deudor.username, 'debo': 0, 'me_deben': 0})
            usuarios_con_deudas[uid]['me_deben'] += g.monto_pendiente

        return Response({
            'pendientes_pago': GastoCompartidoSerializer(pendientes_pago, many=True).data,
            'pendientes_cobro': GastoCompartidoSerializer(pendientes_cobro, many=True).data,
            'total_debo': total_debo,
            'total_me_deben': total_me_deben,
            'usuarios_con_deudas': list(usuarios_con_deudas.values()),
        })


class MarcarGastoPagadoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, gasto_id):
        logger.debug('Marcando gasto compartido %s como pagado user=%s', gasto_id, request.user.id)
        grupos_ids = GrupoMiembro.objects.filter(
            usuario=request.user, grupo__activo=True
        ).values_list('grupo_id', flat=True)
        try:
            gasto = GastoCompartido.objects.select_related(
                'movimiento__concepto', 'usuario_deudor', 'grupo'
            ).get(id=gasto_id, usuario_acreedor=request.user, grupo_id__in=grupos_ids, pagado=False)
        except GastoCompartido.DoesNotExist:
            logger.warning('GastoCompartido %s no encontrado user=%s', gasto_id, request.user.id)
            return Response({'detail': 'Gasto compartido no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        nombre_gasto = gasto.movimiento.nombre if gasto.movimiento else 'Liquidación de deudas'
        concepto_nombre = (
            gasto.movimiento.concepto.nombre
            if gasto.movimiento and gasto.movimiento.concepto
            else 'sin concepto'
        )

        with transaction.atomic():
            gasto.pagado = True
            gasto.save()

            concepto_cobro, _ = Concepto.objects.get_or_create(
                nombre='Cobro de deuda', usuario=request.user,
                defaults={'tipo': Concepto.TIPO_INGRESO, 'activo': True, 'grupo': None},
            )
            Movimiento.objects.create(
                tipo=Movimiento.TIPO_INGRESO,
                nombre=f'Cobro: {nombre_gasto}',
                detalle=f'Pago recibido de {gasto.usuario_deudor.username} por "{concepto_nombre}".',
                monto=gasto.monto_pendiente,
                concepto=concepto_cobro,
                usuario=request.user,
                grupo=None,
                fecha_hora=timezone.now(),
            )
            concepto_pago, _ = Concepto.objects.get_or_create(
                nombre='Pago de deuda', usuario=gasto.usuario_deudor,
                defaults={'tipo': Concepto.TIPO_GASTO, 'activo': True, 'grupo': None},
            )
            Movimiento.objects.create(
                tipo=Movimiento.TIPO_GASTO,
                nombre=f'Pago: {nombre_gasto}',
                detalle=f'Pago realizado a {request.user.username} por "{concepto_nombre}".',
                monto=gasto.monto_pendiente,
                concepto=concepto_pago,
                usuario=gasto.usuario_deudor,
                grupo=None,
                fecha_hora=timezone.now(),
            )
            Notificacion.objects.create(
                titulo=f'{request.user.username} marcó como pagado el gasto compartido de ${gasto.monto_pendiente:,} por {concepto_nombre}.'.replace(',', '.'),
                tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                referencia_id=gasto.movimiento_id,
                usuario=gasto.usuario_deudor,
            )

        logger.info('GastoCompartido %s marcado como pagado monto=%s user=%s deudor=%s', gasto_id, gasto.monto_pendiente, request.user.id, gasto.usuario_deudor_id)
        return Response({'detail': 'Gasto marcado como pagado.'})


class LiquidarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        otro_usuario_id = request.data.get('otro_usuario_id')
        logger.debug('Liquidando deudas entre user=%s y otro_usuario=%s', request.user.id, otro_usuario_id)
        if not otro_usuario_id:
            return Response({'detail': 'otro_usuario_id es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            otro_usuario = User.objects.get(id=otro_usuario_id)
        except User.DoesNotExist:
            logger.warning('Usuario %s no encontrado para liquidar user=%s', otro_usuario_id, request.user.id)
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        grupos_ids = list(
            GrupoMiembro.objects.filter(usuario=request.user, grupo__activo=True).values_list('grupo_id', flat=True)
        )
        me_deben_qs = GastoCompartido.objects.filter(
            usuario_acreedor=request.user, usuario_deudor=otro_usuario,
            grupo_id__in=grupos_ids, pagado=False,
        )
        debo_qs = GastoCompartido.objects.filter(
            usuario_acreedor=otro_usuario, usuario_deudor=request.user,
            grupo_id__in=grupos_ids, pagado=False,
        )
        total_me_deben = me_deben_qs.aggregate(t=Sum('monto_pendiente'))['t'] or 0
        total_debo = debo_qs.aggregate(t=Sum('monto_pendiente'))['t'] or 0

        if total_me_deben == 0 and total_debo == 0:
            logger.warning('Sin deudas pendientes entre user=%s y user=%s', request.user.id, otro_usuario_id)
            return Response({'detail': f'No hay deudas pendientes con {otro_usuario.username}.'}, status=status.HTTP_400_BAD_REQUEST)

        neto = total_me_deben - total_debo
        primer_gasto = me_deben_qs.first() or debo_qs.first()
        grupo_liquidacion = primer_gasto.grupo

        with transaction.atomic():
            me_deben_qs.update(pagado=True)
            debo_qs.update(pagado=True)

            if neto != 0:
                acreedor = request.user if neto > 0 else otro_usuario
                deudor = otro_usuario if neto > 0 else request.user
                monto_neto = abs(neto)
                GastoCompartido.objects.create(
                    movimiento=None,
                    usuario_acreedor=acreedor,
                    usuario_deudor=deudor,
                    monto_pendiente=monto_neto,
                    grupo=grupo_liquidacion,
                )
                Notificacion.objects.create(
                    titulo=(
                        f'{request.user.username} liquidó las deudas contigo. '
                        f'{"Te debe" if deudor == otro_usuario else "Le debes"} '
                        f'${monto_neto:,}.'
                    ).replace(',', '.'),
                    tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                    referencia_id=None,
                    usuario=otro_usuario,
                )
            else:
                Notificacion.objects.create(
                    titulo=f'{request.user.username} liquidó las deudas contigo. ¡Están a mano!',
                    tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                    referencia_id=None,
                    usuario=otro_usuario,
                )

        logger.info('Liquidación completada user=%s otro=%s neto=%s', request.user.id, otro_usuario_id, neto)
        if neto == 0:
            msg = f'¡Liquidado! Tú y {otro_usuario.username} quedan a mano.'
        elif neto > 0:
            msg = f'Liquidado. {otro_usuario.username} te debe ${abs(neto):,} neto.'.replace(',', '.')
        else:
            msg = f'Liquidado. Le debes ${abs(neto):,} neto a {otro_usuario.username}.'.replace(',', '.')
        return Response({'detail': msg, 'neto': neto})


# ── Asistente de división ───────────────────────────────────────────────────

class SplitConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SplitConfirmInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        grupo_id = data['grupo_id']
        monto_total = data['monto_total']
        concepto_nombre = (data.get('concepto_nombre') or 'División de cuenta').strip()
        distribuciones = data['distribuciones']
        payer_id = data.get('payer_id') or request.user.id

        logger.debug('SplitConfirm grupo=%s monto=%s concepto=%s pagador=%s user=%s distribuciones=%d',
                     grupo_id, monto_total, concepto_nombre, payer_id, request.user.id, len(distribuciones))

        try:
            grupo = Grupo.objects.get(id=grupo_id, activo=True)
        except Grupo.DoesNotExist:
            logger.warning('Grupo %s no encontrado en SplitConfirm user=%s', grupo_id, request.user.id)
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if not GrupoMiembro.objects.filter(usuario=request.user, grupo=grupo).exists():
            logger.warning('User=%s no pertenece al grupo=%s en SplitConfirm', request.user.id, grupo_id)
            return Response({'detail': 'No perteneces a este grupo.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            payer = User.objects.get(id=payer_id)
        except User.DoesNotExist:
            return Response({'detail': 'El pagador no existe.'}, status=status.HTTP_400_BAD_REQUEST)
        if not GrupoMiembro.objects.filter(usuario=payer, grupo=grupo).exists():
            return Response({'detail': 'El pagador no es miembro del grupo.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            concepto_grupo, _ = Concepto.objects.get_or_create(
                grupo=grupo, nombre=concepto_nombre, tipo='Gasto',
                defaults={'activo': True, 'usuario': None},
            )
            concepto_personal, _ = Concepto.objects.get_or_create(
                usuario=payer, nombre=concepto_nombre, tipo='Gasto',
                defaults={'activo': True, 'grupo': None},
            )
            Movimiento.objects.create(
                tipo='Gasto', nombre=concepto_nombre,
                detalle='División de gastos (pagador)',
                monto=monto_total, concepto=concepto_personal,
                usuario=payer, grupo=None, fecha_hora=timezone.now(),
            )
            mov = Movimiento.objects.create(
                tipo='Gasto', nombre=concepto_nombre,
                detalle='Asistente de división de gastos',
                monto=monto_total, concepto=concepto_grupo,
                usuario=payer, grupo=grupo, fecha_hora=timezone.now(),
            )
            gastos_creados = []
            for d in distribuciones:
                if str(d['usuario_id']) == str(payer.id):
                    continue
                monto_deudor = int(d['monto'])
                try:
                    deudor = User.objects.get(id=d['usuario_id'])
                except User.DoesNotExist:
                    continue
                if not GrupoMiembro.objects.filter(usuario=deudor, grupo=grupo).exists():
                    continue
                GastoCompartido.objects.create(
                    movimiento=mov,
                    usuario_acreedor=payer,
                    usuario_deudor=deudor,
                    monto_pendiente=monto_deudor,
                    grupo=grupo,
                )
                Notificacion.objects.create(
                    titulo=(
                        f'{payer.username} te asignó ${monto_deudor:,} '
                        f'en "{concepto_nombre}" ({grupo.nombre}).'
                    ).replace(',', '.'),
                    tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                    referencia_id=mov.id,
                    usuario=deudor,
                )
                gastos_creados.append({'username': deudor.username, 'monto': monto_deudor})

            if str(payer.id) != str(request.user.id):
                Notificacion.objects.create(
                    titulo=(
                        f'{request.user.username} te registró como pagador de '
                        f'${monto_total:,} en "{concepto_nombre}" ({grupo.nombre}).'
                    ).replace(',', '.'),
                    tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                    referencia_id=mov.id,
                    usuario=payer,
                )
            crear_notificaciones_grupo(
                grupo, Notificacion.TIPO_GASTO,
                f'División de cuenta de ${monto_total:,} registrada por {request.user.username}'.replace(',', '.'),
                referencia_id=mov.id, excluir_usuario=request.user,
            )

        logger.info('SplitConfirm completado grupo=%s movimiento=%s monto=%s deudores=%d user=%s',
                    grupo_id, mov.id, monto_total, len(gastos_creados), request.user.id)
        return Response({'ok': True, 'gastos': gastos_creados, 'movimiento_id': str(mov.id)})


# ── Helpers de ahorros ──────────────────────────────────────────────────────

def _get_or_create_concepto_ahorro(user, tipo):
    nombre = 'Ahorro' if tipo == Concepto.TIPO_GASTO else 'Retiro de ahorro'
    concepto, _ = Concepto.objects.get_or_create(
        usuario=user, nombre=nombre, tipo=tipo,
        defaults={'activo': True, 'grupo': None},
    )
    return concepto


# ── Ahorros personales ──────────────────────────────────────────────────────

class MetaAhorroPersonalListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        metas = (
            MetaAhorro.objects
            .filter(usuario=request.user, tipo=MetaAhorro.TIPO_PERSONAL, activa=True)
            .order_by('fecha_limite', 'created_at')
        )
        return Response(MetaAhorroSerializer(metas, many=True).data)

    def post(self, request):
        serializer = MetaAhorroCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meta = serializer.save(tipo=MetaAhorro.TIPO_PERSONAL, usuario=request.user, grupo=None)
        logger.info('MetaAhorro personal creada id=%s nombre=%s user=%s', meta.id, meta.nombre, request.user.id)
        return Response(MetaAhorroSerializer(meta).data, status=status.HTTP_201_CREATED)


class MetaAhorroPersonalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, meta_id):
        try:
            meta = MetaAhorro.objects.get(id=meta_id, usuario=request.user, tipo=MetaAhorro.TIPO_PERSONAL)
        except MetaAhorro.DoesNotExist:
            return Response({'detail': 'Meta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        aportes = meta.aportes.select_related('usuario').order_by('-fecha')
        data = MetaAhorroSerializer(meta).data
        data['aportes'] = AporteAhorroSerializer(aportes, many=True).data
        return Response(data)

    def patch(self, request, meta_id):
        try:
            meta = MetaAhorro.objects.get(id=meta_id, usuario=request.user, tipo=MetaAhorro.TIPO_PERSONAL)
        except MetaAhorro.DoesNotExist:
            return Response({'detail': 'Meta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = MetaAhorroCreateSerializer(meta, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MetaAhorroSerializer(meta).data)


class MetaAhorroPersonalAportarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, meta_id):
        try:
            meta = MetaAhorro.objects.get(id=meta_id, usuario=request.user, tipo=MetaAhorro.TIPO_PERSONAL, activa=True)
        except MetaAhorro.DoesNotExist:
            logger.warning('MetaAhorro personal %s no encontrada user=%s', meta_id, request.user.id)
            return Response({'detail': 'Meta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        monto_raw = str(request.data.get('monto', '0')).replace('.', '').replace(',', '')
        try:
            monto = int(monto_raw)
            assert monto > 0
        except (ValueError, AssertionError):
            logger.warning('Monto inválido "%s" en aporte meta=%s user=%s', monto_raw, meta_id, request.user.id)
            return Response({'detail': 'Monto inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            concepto = _get_or_create_concepto_ahorro(request.user, Concepto.TIPO_GASTO)
            mov = Movimiento.objects.create(
                tipo=Movimiento.TIPO_GASTO,
                nombre=f'Ahorro: {meta.nombre}',
                detalle='Aporte a meta de ahorro',
                monto=monto, concepto=concepto,
                usuario=request.user, grupo=None,
                fecha_hora=timezone.now(),
            )
            AporteAhorro.objects.create(
                meta=meta, usuario=request.user,
                monto=monto, fecha=timezone.now(), movimiento=mov,
            )

        logger.info('Aporte a MetaAhorro personal meta=%s monto=%s user=%s', meta_id, monto, request.user.id)
        return Response(MetaAhorroSerializer(meta).data, status=status.HTTP_201_CREATED)


class MetaAhorroPersonalRetirarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, meta_id):
        try:
            meta = MetaAhorro.objects.get(id=meta_id, usuario=request.user, tipo=MetaAhorro.TIPO_PERSONAL, activa=True)
        except MetaAhorro.DoesNotExist:
            logger.warning('MetaAhorro personal %s no encontrada para retiro user=%s', meta_id, request.user.id)
            return Response({'detail': 'Meta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        monto_raw = str(request.data.get('monto', '0')).replace('.', '').replace(',', '')
        try:
            monto = int(monto_raw)
            ahorrado = meta.aportes.aggregate(t=Sum('monto'))['t'] or 0
            assert 0 < monto <= ahorrado
        except (ValueError, AssertionError):
            logger.warning('Monto retiro inválido "%s" meta=%s ahorrado=%s user=%s', monto_raw, meta_id, locals().get('ahorrado', '?'), request.user.id)
            return Response({'detail': 'Monto de retiro inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            concepto = _get_or_create_concepto_ahorro(request.user, Concepto.TIPO_INGRESO)
            mov = Movimiento.objects.create(
                tipo=Movimiento.TIPO_INGRESO,
                nombre=f'Retiro de ahorro: {meta.nombre}',
                detalle='Retiro de meta de ahorro',
                monto=monto, concepto=concepto,
                usuario=request.user, grupo=None,
                fecha_hora=timezone.now(),
            )
            AporteAhorro.objects.create(
                meta=meta, usuario=request.user,
                monto=-monto, fecha=timezone.now(), movimiento=mov,
            )

        logger.info('Retiro de MetaAhorro personal meta=%s monto=%s user=%s', meta_id, monto, request.user.id)
        return Response(MetaAhorroSerializer(meta).data)


class MetaAhorroPersonalArchivarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, meta_id):
        try:
            meta = MetaAhorro.objects.get(id=meta_id, usuario=request.user, tipo=MetaAhorro.TIPO_PERSONAL)
        except MetaAhorro.DoesNotExist:
            logger.warning('MetaAhorro personal %s no encontrada para archivar user=%s', meta_id, request.user.id)
            return Response({'detail': 'Meta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        meta.activa = False
        meta.save()
        logger.info('MetaAhorro personal archivada id=%s nombre=%s user=%s', meta_id, meta.nombre, request.user.id)
        return Response({'detail': f'Meta "{meta.nombre}" archivada.'})


# ── Tarjetas ────────────────────────────────────────────────────────────────

class TarjetaListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tarjetas = list(Tarjeta.objects.filter(usuario=request.user, activa=True).order_by('-created_at'))
        data = TarjetaSerializer(tarjetas, many=True).data
        for item, tarjeta in zip(data, tarjetas):
            if tarjeta.tipo == Tarjeta.TIPO_DEBITO:
                ingresos = Movimiento.objects.filter(tarjeta=tarjeta, tipo=Movimiento.TIPO_INGRESO).aggregate(s=Sum('monto'))['s'] or 0
                gastos = Movimiento.objects.filter(tarjeta=tarjeta, tipo=Movimiento.TIPO_GASTO).aggregate(s=Sum('monto'))['s'] or 0
                item['saldo_disponible'] = ingresos - gastos
            else:
                item['saldo_disponible'] = None
        return Response(data)

    def post(self, request):
        serializer = TarjetaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tarjeta = serializer.save(usuario=request.user)
        logger.info('Tarjeta creada id=%s tipo=%s user=%s', tarjeta.id, tarjeta.tipo, request.user.id)
        return Response(TarjetaSerializer(tarjeta).data, status=status.HTTP_201_CREATED)


class TarjetaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, card_id):
        try:
            tarjeta = Tarjeta.objects.get(id=card_id, usuario=request.user, activa=True)
        except Tarjeta.DoesNotExist:
            return Response({'detail': 'Tarjeta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        movimientos = (
            Movimiento.objects
            .filter(tarjeta=tarjeta)
            .select_related('concepto')
            .order_by('-fecha_hora')
        )
        paginator = PageNumberPagination()
        paginator.page_size = 15
        page = paginator.paginate_queryset(movimientos, request)
        total_gastos = movimientos.filter(tipo='Gasto').aggregate(t=Sum('monto'))['t'] or 0
        total_ingresos = movimientos.filter(tipo='Ingreso').aggregate(t=Sum('monto'))['t'] or 0
        response = paginator.get_paginated_response(MovimientoSerializer(page, many=True).data)
        response.data['tarjeta'] = TarjetaSerializer(tarjeta).data
        response.data['total_gastos'] = total_gastos
        response.data['total_ingresos'] = total_ingresos
        return response

    def delete(self, request, card_id):
        try:
            tarjeta = Tarjeta.objects.get(id=card_id, usuario=request.user, activa=True)
        except Tarjeta.DoesNotExist:
            logger.warning('Tarjeta %s no encontrada user=%s', card_id, request.user.id)
            return Response({'detail': 'Tarjeta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        tarjeta.activa = False
        tarjeta.save()
        logger.info('Tarjeta eliminada id=%s user=%s', card_id, request.user.id)
        return Response({'detail': 'Tarjeta eliminada.'})


# ── Ahorros grupales ────────────────────────────────────────────────────────

class MetaAhorroGrupalListCreateView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id):
        metas = (
            MetaAhorro.objects
            .filter(grupo_id=group_id, tipo=MetaAhorro.TIPO_GRUPAL, activa=True)
            .order_by('fecha_limite', 'created_at')
        )
        return Response(MetaAhorroSerializer(metas, many=True).data)

    def post(self, request, group_id):
        if not GrupoMiembro.objects.filter(usuario=request.user, grupo_id=group_id, rol=GrupoMiembro.ROL_ADMIN).exists():
            logger.warning('User=%s no es admin del grupo=%s, intento de crear meta grupal', request.user.id, group_id)
            return Response({'detail': 'Solo el administrador puede crear metas grupales.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            grupo = Grupo.objects.get(id=group_id, activo=True)
        except Grupo.DoesNotExist:
            logger.warning('Grupo %s no encontrado para meta grupal user=%s', group_id, request.user.id)
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = MetaAhorroCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meta = serializer.save(tipo=MetaAhorro.TIPO_GRUPAL, usuario=None, grupo=grupo)
        logger.info('MetaAhorro grupal creada id=%s nombre=%s grupo=%s user=%s', meta.id, meta.nombre, group_id, request.user.id)
        notificar = bool(request.data.get('notificar', False))
        if notificar:
            crear_notificaciones_grupo(
                grupo, Notificacion.TIPO_GASTO,
                f'{request.user.username} creó la meta de ahorro grupal "{meta.nombre}".',
                referencia_id=meta.id, excluir_usuario=request.user,
            )
        return Response(MetaAhorroSerializer(meta).data, status=status.HTTP_201_CREATED)


class MetaAhorroGrupalDetailView(APIView):
    permission_classes = [IsGroupMember]

    def get(self, request, group_id, meta_id):
        try:
            meta = MetaAhorro.objects.get(id=meta_id, grupo_id=group_id, tipo=MetaAhorro.TIPO_GRUPAL)
        except MetaAhorro.DoesNotExist:
            return Response({'detail': 'Meta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        aportes = meta.aportes.select_related('usuario').order_by('-fecha')
        ahorrado = aportes.aggregate(t=Sum('monto'))['t'] or 0

        miembros = GrupoMiembro.objects.filter(grupo_id=group_id).select_related('usuario')
        desglose = []
        for mem in miembros:
            monto_mem = aportes.filter(usuario=mem.usuario).aggregate(t=Sum('monto'))['t'] or 0
            if monto_mem > 0:
                desglose.append({
                    'username': mem.usuario.username,
                    'monto': monto_mem,
                    'pct_aporte': round(monto_mem / ahorrado * 100) if ahorrado else 0,
                })
        desglose.sort(key=lambda x: x['monto'], reverse=True)

        data = MetaAhorroSerializer(meta).data
        data['aportes'] = AporteAhorroSerializer(aportes, many=True).data
        data['desglose'] = desglose
        return Response(data)

    def patch(self, request, group_id, meta_id):
        if not GrupoMiembro.objects.filter(usuario=request.user, grupo_id=group_id, rol=GrupoMiembro.ROL_ADMIN).exists():
            return Response({'detail': 'Solo el administrador puede editar metas grupales.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            meta = MetaAhorro.objects.get(id=meta_id, grupo_id=group_id, tipo=MetaAhorro.TIPO_GRUPAL)
        except MetaAhorro.DoesNotExist:
            return Response({'detail': 'Meta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = MetaAhorroCreateSerializer(meta, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MetaAhorroSerializer(meta).data)


class MetaAhorroGrupalAportarView(APIView):
    permission_classes = [IsGroupMember]

    def post(self, request, group_id, meta_id):
        try:
            meta = MetaAhorro.objects.get(id=meta_id, grupo_id=group_id, tipo=MetaAhorro.TIPO_GRUPAL, activa=True)
        except MetaAhorro.DoesNotExist:
            logger.warning('MetaAhorro grupal %s no encontrada grupo=%s user=%s', meta_id, group_id, request.user.id)
            return Response({'detail': 'Meta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            grupo = Grupo.objects.get(id=group_id, activo=True)
        except Grupo.DoesNotExist:
            logger.warning('Grupo %s no encontrado en aporte meta grupal user=%s', group_id, request.user.id)
            return Response({'detail': 'Grupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        monto_raw = str(request.data.get('monto', '0')).replace('.', '').replace(',', '')
        try:
            monto = int(monto_raw)
            assert monto > 0
        except (ValueError, AssertionError):
            logger.warning('Monto inválido "%s" en aporte meta grupal=%s user=%s', monto_raw, meta_id, request.user.id)
            return Response({'detail': 'Monto inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            concepto = _get_or_create_concepto_ahorro(request.user, Concepto.TIPO_GASTO)
            mov = Movimiento.objects.create(
                tipo=Movimiento.TIPO_GASTO,
                nombre=f'Ahorro grupal: {meta.nombre}',
                detalle=f'Aporte a meta de ahorro del grupo {grupo.nombre}',
                monto=monto, concepto=concepto,
                usuario=request.user, grupo=None,
                fecha_hora=timezone.now(),
            )
            AporteAhorro.objects.create(
                meta=meta, usuario=request.user,
                monto=monto, fecha=timezone.now(), movimiento=mov,
            )
            ahorrado = meta.aportes.aggregate(t=Sum('monto'))['t'] or 0
            if meta.monto_objetivo and ahorrado >= meta.monto_objetivo:
                crear_notificaciones_grupo(
                    grupo, Notificacion.TIPO_GASTO,
                    f'¡La meta de ahorro "{meta.nombre}" fue completada!',
                    referencia_id=meta.id,
                )

        logger.info('Aporte a MetaAhorro grupal meta=%s monto=%s grupo=%s user=%s', meta_id, monto, group_id, request.user.id)
        return Response(MetaAhorroSerializer(meta).data, status=status.HTTP_201_CREATED)


class MetaAhorroGrupalArchivarView(APIView):
    permission_classes = [IsGroupMember]

    def post(self, request, group_id, meta_id):
        if not GrupoMiembro.objects.filter(usuario=request.user, grupo_id=group_id, rol=GrupoMiembro.ROL_ADMIN).exists():
            logger.warning('User=%s no es admin del grupo=%s, intento de archivar meta grupal', request.user.id, group_id)
            return Response({'detail': 'Solo el administrador puede archivar metas grupales.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            meta = MetaAhorro.objects.get(id=meta_id, grupo_id=group_id, tipo=MetaAhorro.TIPO_GRUPAL)
        except MetaAhorro.DoesNotExist:
            logger.warning('MetaAhorro grupal %s no encontrada para archivar grupo=%s user=%s', meta_id, group_id, request.user.id)
            return Response({'detail': 'Meta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        meta.activa = False
        meta.save()
        logger.info('MetaAhorro grupal archivada id=%s nombre=%s grupo=%s user=%s', meta_id, meta.nombre, group_id, request.user.id)
        return Response({'detail': f'Meta "{meta.nombre}" archivada.'})
