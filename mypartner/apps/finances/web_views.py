import csv
import io
import json
import logging
import os
from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from apps.groups.models import Grupo, GrupoMiembro
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo

from apps.documents.models import Documento, ALLOWED_EXTENSIONS as DOC_ALLOWED_EXTENSIONS
from .models import (
    AporteAhorro, BANCOS_CHILE, Concepto, DivisionPresupuesto, GastoCompartido,
    MetaAhorro, Movimiento, RegistroPresupuesto, ReplicaGrupal, Tarjeta,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_grupos_usuario(user):
    return (
        GrupoMiembro.objects
        .filter(usuario=user, grupo__activo=True)
        .select_related('grupo')
    )


def _build_miembros_por_grupo(user):
    memberships = _get_grupos_usuario(user)
    result = {}
    for m in memberships:
        otros = (
            GrupoMiembro.objects
            .filter(grupo=m.grupo)
            .exclude(usuario=user)
            .select_related('usuario')
        )
        result[str(m.grupo_id)] = [
            {'id': str(o.usuario_id), 'username': o.usuario.username}
            for o in otros
        ]
    return result


@login_required
def dashboard_view(request):
    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    vista = request.GET.get('vista', 'historico')
    if vista not in ('mensual', 'historico'):
        vista = 'historico'

    movimientos_qs = Movimiento.objects.filter(usuario=request.user, grupo__isnull=True)
    if vista == 'mensual':
        movimientos_qs = movimientos_qs.filter(
            fecha_hora__date__gte=mes_inicio, fecha_hora__date__lte=hoy
        )
        presupuesto_acum = (
            RegistroPresupuesto.objects
            .filter(usuario=request.user, grupo__isnull=True, tipo='Gasto',
                    fecha__gte=mes_inicio, fecha__lte=hoy)
            .aggregate(t=Sum('monto'))['t'] or 0
        )
    else:
        presupuesto_acum = (
            RegistroPresupuesto.objects
            .filter(usuario=request.user, grupo__isnull=True, tipo='Gasto')
            .aggregate(t=Sum('monto'))['t'] or 0
        )

    _conceptos_ahorro = ('Ahorro', 'Retiro de ahorro')
    gasto_total = (
        movimientos_qs.filter(tipo='Gasto')
        .exclude(concepto__nombre__in=_conceptos_ahorro)
        .aggregate(t=Sum('monto'))['t'] or 0
    )
    ingreso_total = (
        movimientos_qs.filter(tipo='Ingreso')
        .exclude(concepto__nombre__in=_conceptos_ahorro)
        .aggregate(t=Sum('monto'))['t'] or 0
    )
    saldo_restante = ingreso_total - gasto_total
    desviacion = presupuesto_acum - gasto_total

    gastos_concepto = (
        movimientos_qs.filter(tipo='Gasto')
        .exclude(concepto__nombre__in=_conceptos_ahorro)
        .values('concepto__nombre')
        .annotate(total=Sum('monto'))
        .order_by('-total')
    )
    chart_labels, chart_data = [], []
    items = list(gastos_concepto)
    if len(items) <= 5:
        for item in items:
            chart_labels.append(item['concepto__nombre'] or 'Desconocido')
            chart_data.append(item['total'])
    else:
        for item in items[:5]:
            chart_labels.append(item['concepto__nombre'] or 'Desconocido')
            chart_data.append(item['total'])
        otros = sum(i['total'] for i in items[5:])
        if otros:
            chart_labels.append('Otros')
            chart_data.append(otros)

    ultimos = (
        Movimiento.objects
        .filter(usuario=request.user, grupo__isnull=True)
        .select_related('concepto')
        .order_by('-fecha_hora')[:5]
    )

    conceptos_gasto = Concepto.objects.filter(usuario=request.user, tipo='Gasto', activo=True)
    conceptos_ingreso = Concepto.objects.filter(usuario=request.user, tipo='Ingreso', activo=True)

    memberships = _get_grupos_usuario(request.user)
    miembros_por_grupo = _build_miembros_por_grupo(request.user)

    grupos_resumen = []
    for m in memberships:
        gasto_mes = (
            Movimiento.objects
            .filter(grupo=m.grupo, tipo='Gasto',
                    fecha_hora__date__gte=mes_inicio, fecha_hora__date__lte=hoy)
            .aggregate(t=Sum('monto'))['t'] or 0
        )
        grupos_resumen.append({'grupo': m.grupo, 'gasto_mes': gasto_mes})

    grupos_ids = list(memberships.values_list('grupo_id', flat=True))
    pendientes_count = GastoCompartido.objects.filter(
        usuario_deudor=request.user, grupo_id__in=grupos_ids, pagado=False
    ).count()

    tarjetas = list(Tarjeta.objects.filter(usuario=request.user, activa=True).order_by('-created_at'))
    ultimo_mov_con_tarjeta = (
        Movimiento.objects
        .filter(usuario=request.user, grupo__isnull=True, tarjeta__isnull=False, tarjeta__activa=True)
        .order_by('-fecha_hora')
        .values_list('tarjeta_id', flat=True)
        .first()
    )
    if ultimo_mov_con_tarjeta:
        ultima_tarjeta_id = str(ultimo_mov_con_tarjeta)
    elif tarjetas:
        ultima_tarjeta_id = str(tarjetas[0].id)
    else:
        ultima_tarjeta_id = ''

    return render(request, 'finances/dashboard.html', {
        'gasto_total': gasto_total,
        'ingreso_total': ingreso_total,
        'saldo_restante': saldo_restante,
        'desviacion': desviacion,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'ultimos_movimientos': ultimos,
        'conceptos_gasto': conceptos_gasto,
        'conceptos_ingreso': conceptos_ingreso,
        'grupos_resumen': grupos_resumen,
        'miembros_por_grupo_json': json.dumps(miembros_por_grupo),
        'pendientes_count': pendientes_count,
        'hoy': hoy,
        'vista': vista,
        'tiene_grupos': memberships.exists(),
        'grupos_usuario': [{'id': str(m.grupo_id), 'nombre': m.grupo.nombre} for m in memberships],
        'tarjetas': tarjetas,
        'ultima_tarjeta_id': ultima_tarjeta_id,
        'tarjetas_tipos_json': json.dumps({str(t.id): t.tipo for t in tarjetas}),
    })


@login_required
def budget_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            tipo = request.POST.get('tipo')
            concepto_id = request.POST.get('concepto')
            nombre = request.POST.get('nombre', '').strip()
            detalle = request.POST.get('detalle', '').strip()
            fecha_str = request.POST.get('fecha', '')
            monto_str = request.POST.get('monto', '0').replace('.', '').replace(',', '')
            periodicidad = request.POST.get('periodicidad', 'Puntual')
            if periodicidad not in ('Puntual', 'Mensual', 'Anual'):
                periodicidad = 'Puntual'
            fecha_fin_str = request.POST.get('fecha_fin', '').strip()
            fecha_fin = None
            if fecha_fin_str and periodicidad in ('Mensual', 'Anual'):
                try:
                    fecha_fin = date.fromisoformat(fecha_fin_str)
                except ValueError:
                    pass

            dividir_presupuesto = request.POST.get('dividir_presupuesto') == '1'
            grupo_division_id = request.POST.get('grupo_division_id', '').strip()
            divisiones_json_str = request.POST.get('divisiones_json', '[]')

            try:
                concepto = Concepto.objects.get(id=concepto_id, usuario=request.user, activo=True)
                monto = int(monto_str)
                assert monto > 0 and nombre

                campos_base = dict(
                    tipo=tipo, nombre=nombre, fecha=fecha_str,
                    periodicidad=periodicidad, fecha_fin=fecha_fin,
                )

                with transaction.atomic():
                    if dividir_presupuesto and grupo_division_id:
                        if not GrupoMiembro.objects.filter(
                            usuario=request.user, grupo_id=grupo_division_id, grupo__activo=True
                        ).exists():
                            raise ValueError('No eres miembro del grupo seleccionado.')

                        grupo_div = Grupo.objects.get(id=grupo_division_id, activo=True)
                        divisiones_data = json.loads(divisiones_json_str)
                        otros_total = sum(int(d.get('monto', 0)) for d in divisiones_data)
                        monto_propietario = monto - otros_total

                        if monto_propietario < 0:
                            raise ValueError('La suma de montos supera el total del presupuesto.')

                        # 1. Presupuesto en el grupo (monto total)
                        concepto_grupo, _ = Concepto.objects.get_or_create(
                            grupo=grupo_div, nombre=concepto.nombre, tipo=tipo,
                            defaults={'activo': True, 'usuario': None},
                        )
                        detalle_ref = f'Grupo: {grupo_div.nombre} · Total: ${monto:,}'.replace(',', '.')
                        detalle_grupo = f'{detalle_ref}\n{detalle}'.strip() if detalle else detalle_ref
                        registro_grupo = RegistroPresupuesto.objects.create(
                            **campos_base, concepto=concepto_grupo,
                            detalle=detalle_grupo, monto=monto,
                            usuario=None, grupo=grupo_div,
                        )

                        # 2. Presupuesto personal del propietario (su porción)
                        detalle_personal = f'{detalle_ref}\n{detalle}'.strip() if detalle else detalle_ref
                        RegistroPresupuesto.objects.create(
                            **campos_base, concepto=concepto,
                            detalle=detalle_personal, monto=monto_propietario,
                            usuario=request.user, grupo=None,
                        )

                        # 3. Presupuesto personal de cada otro usuario (su porción)
                        usuarios_div = []
                        for d in divisiones_data:
                            user_div = User.objects.get(id=d['usuario_id'])
                            if not GrupoMiembro.objects.filter(
                                usuario=user_div, grupo=grupo_div, grupo__activo=True
                            ).exists():
                                raise ValueError(f'{user_div.username} no es miembro del grupo.')
                            concepto_div, _ = Concepto.objects.get_or_create(
                                usuario=user_div, nombre=concepto.nombre, tipo=tipo,
                                defaults={'activo': True, 'grupo': None},
                            )
                            RegistroPresupuesto.objects.create(
                                **campos_base, concepto=concepto_div,
                                detalle=detalle_personal, monto=int(d['monto']),
                                usuario=user_div, grupo=None,
                            )
                            usuarios_div.append((user_div, int(d['monto'])))

                        # 4. DivisionPresupuesto apuntando al presupuesto del grupo
                        divisiones_objs = [
                            DivisionPresupuesto(
                                registro_presupuesto=registro_grupo,
                                grupo=grupo_div, usuario=request.user,
                                monto=monto_propietario,
                            )
                        ]
                        for user_div, monto_div in usuarios_div:
                            divisiones_objs.append(DivisionPresupuesto(
                                registro_presupuesto=registro_grupo,
                                grupo=grupo_div, usuario=user_div,
                                monto=monto_div,
                            ))
                        DivisionPresupuesto.objects.bulk_create(divisiones_objs)

                        # 5. Notificaciones a los otros usuarios
                        for user_div, monto_div in usuarios_div:
                            Notificacion.objects.create(
                                titulo=(
                                    f'{request.user.username} te asignó '
                                    f'${monto_div:,} del presupuesto "{nombre}" '
                                    f'en {grupo_div.nombre}'
                                ).replace(',', '.'),
                                tipo=Notificacion.TIPO_PRESUPUESTO,
                                referencia_id=registro_grupo.id,
                                usuario=user_div,
                            )

                    else:
                        # Sin división: presupuesto personal simple
                        RegistroPresupuesto.objects.create(
                            **campos_base, concepto=concepto,
                            detalle=detalle, monto=monto,
                            usuario=request.user, grupo=None,
                        )

                logger.info('PresupuestoWeb creado user=%s tipo=%s nombre=%s monto=%s dividir=%s', request.user.id, tipo, nombre, monto, dividir_presupuesto)
                messages.success(request, 'Registro de presupuesto agregado.')
            except Exception as e:
                logger.error('Error creando presupuesto web user=%s: %s', request.user.id, e, exc_info=True)
                messages.error(request, f'Error al agregar registro: {e}')

        elif action == 'modify':
            registro_id = request.POST.get('registro_id')
            monto_str = request.POST.get('monto', '0').replace('.', '').replace(',', '')
            try:
                registro = RegistroPresupuesto.objects.get(id=registro_id, usuario=request.user)
                registro.monto = int(monto_str)
                registro.save()
                logger.info('PresupuestoWeb actualizado id=%s user=%s', registro_id, request.user.id)
                messages.success(request, 'Monto actualizado.')
            except Exception as e:
                logger.error('Error actualizando presupuesto web id=%s user=%s: %s', registro_id, request.user.id, e, exc_info=True)
                messages.error(request, 'Error al modificar.')

        elif action == 'delete':
            registro_id = request.POST.get('registro_id')
            try:
                registro = RegistroPresupuesto.objects.get(id=registro_id, usuario=request.user)
                registro.delete()
                logger.info('PresupuestoWeb eliminado id=%s user=%s', registro_id, request.user.id)
                messages.success(request, 'Registro eliminado.')
            except Exception as e:
                logger.error('Error eliminando presupuesto web id=%s user=%s: %s', registro_id, request.user.id, e, exc_info=True)
                messages.error(request, 'Error al eliminar.')

        return redirect('finances-budget')

    hoy = date.today()
    MESES_ES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

    mes_filtro = request.GET.get('mes', hoy.strftime('%Y-%m'))
    try:
        anio, mes = mes_filtro.split('-')
        anio, mes = int(anio), int(mes)
    except (ValueError, AttributeError):
        anio, mes = hoy.year, hoy.month
        mes_filtro = f'{anio:04d}-{mes:02d}'

    prev_offset = mes - 2
    prev_mes = f'{anio + prev_offset // 12:04d}-{prev_offset % 12 + 1:02d}'
    next_offset = mes
    next_mes = f'{anio + next_offset // 12:04d}-{next_offset % 12 + 1:02d}'

    base_qs = RegistroPresupuesto.objects.filter(usuario=request.user, grupo__isnull=True).filter(
        Q(periodicidad='Mensual', fecha__year__lt=anio) |
        Q(periodicidad='Mensual', fecha__year=anio, fecha__month__lte=mes) |
        Q(periodicidad='Anual', fecha__month=mes, fecha__year__lte=anio) |
        Q(periodicidad='Puntual', fecha__year=anio, fecha__month=mes)
    ).filter(
        Q(fecha_fin__isnull=True) |
        Q(fecha_fin__year__gt=anio) |
        Q(fecha_fin__year=anio, fecha_fin__month__gte=mes)
    )

    registros = base_qs.select_related('concepto').prefetch_related('divisiones__usuario').order_by('-tipo', '-monto')
    ingresos = base_qs.filter(tipo='Ingreso').aggregate(t=Sum('monto'))['t'] or 0
    gastos = base_qs.filter(tipo='Gasto').aggregate(t=Sum('monto'))['t'] or 0
    total = ingresos - gastos

    conceptos_gasto = Concepto.objects.filter(usuario=request.user, tipo='Gasto', activo=True)
    conceptos_ingreso = Concepto.objects.filter(usuario=request.user, tipo='Ingreso', activo=True)

    memberships = _get_grupos_usuario(request.user)
    miembros_por_grupo = _build_miembros_por_grupo(request.user)

    return render(request, 'finances/budget.html', {
        'registros': registros, 'total': total,
        'conceptos_gasto': conceptos_gasto, 'conceptos_ingreso': conceptos_ingreso,
        'mes_filtro': mes_filtro, 'mes_nombre': MESES_ES[mes - 1], 'mes_anio': anio,
        'prev_mes': prev_mes, 'next_mes': next_mes,
        'grupos_usuario': [{'id': str(m.grupo_id), 'nombre': m.grupo.nombre} for m in memberships],
        'miembros_por_grupo_json': json.dumps(miembros_por_grupo),
        'tiene_grupos': memberships.exists(),
    })


@login_required
def concepts_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            nombre = request.POST.get('nombre', '').strip()
            tipo = request.POST.get('tipo')
            if nombre and tipo in ('Gasto', 'Ingreso'):
                if Concepto.objects.filter(usuario=request.user, nombre__iexact=nombre, activo=True).exists():
                    logger.warning('ConceptoWeb duplicado "%s" user=%s', nombre, request.user.id)
                    messages.error(request, f'Ya existe un concepto llamado "{nombre}".')
                else:
                    Concepto.objects.create(nombre=nombre, tipo=tipo, usuario=request.user, grupo=None)
                    logger.info('ConceptoWeb creado nombre=%s tipo=%s user=%s', nombre, tipo, request.user.id)
                    messages.success(request, 'Concepto agregado.')
            else:
                logger.warning('ConceptoWeb datos inválidos nombre="%s" tipo="%s" user=%s', nombre, tipo, request.user.id)
                messages.error(request, 'Nombre y tipo son obligatorios.')

        elif action == 'edit':
            concepto_id = request.POST.get('concepto_id')
            nombre = request.POST.get('nombre', '').strip()
            try:
                c = Concepto.objects.get(id=concepto_id, usuario=request.user, activo=True)
                if Concepto.objects.filter(usuario=request.user, nombre__iexact=nombre, activo=True).exclude(id=concepto_id).exists():
                    logger.warning('ConceptoWeb duplicado "%s" al editar id=%s user=%s', nombre, concepto_id, request.user.id)
                    messages.error(request, f'Ya existe un concepto llamado "{nombre}".')
                    return redirect('finances-concepts')
                c.nombre = nombre
                c.save()
                logger.info('ConceptoWeb actualizado id=%s nombre=%s user=%s', concepto_id, nombre, request.user.id)
                messages.success(request, 'Concepto actualizado.')
            except Concepto.DoesNotExist:
                logger.warning('ConceptoWeb %s no encontrado al editar user=%s', concepto_id, request.user.id)
                messages.error(request, 'Concepto no encontrado.')

        elif action == 'delete':
            concepto_id = request.POST.get('concepto_id')
            opcion = request.POST.get('opcion', '')
            try:
                c = Concepto.objects.get(id=concepto_id, usuario=request.user, activo=True)
                if opcion == 'eliminar_movimientos':
                    deleted_count = Movimiento.objects.filter(concepto=c).delete()[0]
                    c.activo = False
                    c.save()
                    logger.info('ConceptoWeb eliminado con %d movimientos id=%s user=%s', deleted_count, concepto_id, request.user.id)
                    messages.success(request, 'Concepto y movimientos eliminados.')
                elif opcion == 'mantener_movimientos':
                    Movimiento.objects.filter(concepto=c).update(concepto=None)
                    c.activo = False
                    c.save()
                    logger.info('ConceptoWeb eliminado, movimientos conservados id=%s user=%s', concepto_id, request.user.id)
                    messages.success(request, 'Concepto eliminado. Movimientos conservados.')
                else:
                    has_mov = Movimiento.objects.filter(concepto=c).exists()
                    if has_mov:
                        return render(request, 'finances/concepts.html', {
                            'conceptos': Concepto.objects.filter(usuario=request.user, activo=True),
                            'concepto_conflicto': c,
                        })
                    c.activo = False
                    c.save()
                    logger.info('ConceptoWeb eliminado id=%s user=%s', concepto_id, request.user.id)
                    messages.success(request, 'Concepto eliminado.')
            except Concepto.DoesNotExist:
                logger.warning('ConceptoWeb %s no encontrado al eliminar user=%s', concepto_id, request.user.id)
                messages.error(request, 'Concepto no encontrado.')

        return redirect('finances-concepts')

    conceptos = Concepto.objects.filter(usuario=request.user, activo=True).order_by('tipo', 'nombre')
    return render(request, 'finances/concepts.html', {'conceptos': conceptos})


@login_required
def movements_view(request):
    qs = (
        Movimiento.objects
        .filter(usuario=request.user, grupo__isnull=True)
        .select_related('concepto')
        .order_by('-fecha_hora')
    )
    concepto_id = request.GET.get('concepto', '')
    if concepto_id:
        qs = qs.filter(concepto_id=concepto_id)

    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get('page', 1))
    conceptos = Concepto.objects.filter(usuario=request.user, activo=True).order_by('nombre')

    return render(request, 'finances/movements.html', {
        'page': page, 'conceptos': conceptos, 'concepto_filtro': concepto_id,
    })


@login_required
def movement_detail_view(request, movement_id):
    mov = get_object_or_404(
        Movimiento.objects.select_related('concepto', 'usuario'),
        id=movement_id, usuario=request.user, grupo__isnull=True,
    )
    replicas = ReplicaGrupal.objects.filter(movimiento_personal=mov).select_related('grupo')
    return render(request, 'finances/movement_detail.html', {
        'movimiento': mov, 'replicas': replicas,
    })


@login_required
def movement_correct_view(request, movement_id):
    if request.method != 'POST':
        return redirect('finances-movement-detail', movement_id=movement_id)

    mov = get_object_or_404(
        Movimiento,
        id=movement_id,
        usuario=request.user,
        grupo__isnull=True,
        tipo=Movimiento.TIPO_GASTO,
    )

    monto_final_str = request.POST.get('monto_final', '0').replace('.', '').replace(',', '')
    logger.debug('CorreccionWeb movimiento=%s monto_final=%s user=%s', movement_id, monto_final_str, request.user.id)
    try:
        monto_final = int(monto_final_str)
        assert monto_final > 0
    except (ValueError, AssertionError):
        logger.warning('CorreccionWeb monto inválido "%s" movimiento=%s user=%s', monto_final_str, movement_id, request.user.id)
        messages.error(request, 'Monto inválido.')
        return redirect('finances-movement-detail', movement_id=movement_id)

    diferencia = monto_final - mov.monto
    if diferencia == 0:
        messages.warning(request, 'El monto es igual al original, no hay corrección que registrar.')
        return redirect('finances-movement-detail', movement_id=movement_id)

    tipo_correccion = Movimiento.TIPO_GASTO if diferencia > 0 else Movimiento.TIPO_INGRESO
    monto_correccion = abs(diferencia)
    monto_original = mov.monto

    with transaction.atomic():
        Movimiento.objects.create(
            tipo=tipo_correccion,
            nombre='Corrección de gasto',
            detalle=f'Corrección de «{mov.nombre}»: ${monto_original:,} → ${monto_final:,}'.replace(',', '.'),
            monto=monto_correccion,
            concepto=None,
            usuario=request.user,
            grupo=None,
            fecha_hora=timezone.now(),
        )

        replicas = (
            ReplicaGrupal.objects
            .filter(movimiento_personal=mov)
            .select_related('movimiento_grupo')
        )
        for replica in replicas:
            mov_grupo = replica.movimiento_grupo
            compartidos = (
                GastoCompartido.objects
                .filter(movimiento=mov_grupo, pagado=False)
                .select_related('usuario_deudor')
            )
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

    logger.info('CorreccionWeb registrada movimiento=%s original=%s final=%s diferencia=%s user=%s', movement_id, monto_original, monto_final, diferencia, request.user.id)
    signo = '+' if diferencia > 0 else '-'
    messages.success(
        request,
        f'Corrección registrada: {signo}${monto_correccion:,} como {tipo_correccion.lower()}.'.replace(',', '.')
    )
    return redirect('finances-movement-detail', movement_id=movement_id)


@login_required
def export_csv_view(request):
    movimientos = (
        Movimiento.objects
        .filter(usuario=request.user, grupo__isnull=True)
        .select_related('concepto')
        .order_by('-fecha_hora')
    )
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Tipo', 'Concepto', 'Nombre', 'Detalle', 'Monto', 'Fecha y hora'])
    for m in movimientos:
        c_nombre = m.concepto.nombre if m.concepto and m.concepto.activo else 'Desconocido'
        writer.writerow([m.tipo, c_nombre, m.nombre, m.detalle, m.monto,
                         m.fecha_hora.strftime('%d/%m/%Y %H:%M')])
    content = '﻿' + output.getvalue()
    response = HttpResponse(content, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="movimientos.csv"'
    return response


@login_required
def add_movement_view(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        nombre = request.POST.get('nombre', '').strip()
        detalle = request.POST.get('detalle', '').strip()
        concepto_id = request.POST.get('concepto', '').strip()
        monto_str = request.POST.get('monto', '0').replace('.', '').replace(',', '')
        registrar_en_grupo = request.POST.get('registrar_en_grupo') == '1'
        grupo_id = request.POST.get('grupo_id', '').strip()
        es_compartido = request.POST.get('es_compartido') == '1'
        usuario_deudor_id = request.POST.get('usuario_deudor', '').strip()
        monto_compartido_str = request.POST.get('monto_compartido', '').replace('.', '').replace(',', '')
        tarjeta_id = request.POST.get('tarjeta_id', '').strip()
        cuotas_str = request.POST.get('cuotas', '').strip()
        logger.debug('MovimientoWeb tipo=%s nombre=%s monto=%s grupo=%s compartido=%s user=%s', tipo, nombre, monto_str, grupo_id, es_compartido, request.user.id)

        comprobante = request.FILES.get('comprobante')
        grupo_doc = None

        if comprobante:
            _ext = os.path.splitext(comprobante.name)[1].lstrip('.').lower()
            if _ext not in DOC_ALLOWED_EXTENSIONS:
                messages.warning(request, f'Formato de comprobante no permitido ({_ext}). Solo: {", ".join(DOC_ALLOWED_EXTENSIONS)}.')
                comprobante = None
            elif comprobante.size > 10 * 1024 * 1024:
                messages.warning(request, 'El comprobante supera los 10 MB y no fue adjuntado.')
                comprobante = None

        try:
            monto = int(monto_str)
            assert monto > 0 and nombre

            concepto = None
            if concepto_id:
                try:
                    concepto = Concepto.objects.get(id=concepto_id, usuario=request.user, activo=True)
                except Concepto.DoesNotExist:
                    pass

            tarjeta = None
            if tarjeta_id:
                try:
                    tarjeta = Tarjeta.objects.get(id=tarjeta_id, usuario=request.user, activa=True)
                except Tarjeta.DoesNotExist:
                    pass

            cuotas = None
            if tarjeta and tarjeta.tipo == Tarjeta.TIPO_CREDITO and cuotas_str.isdigit():
                cuotas = max(1, int(cuotas_str))

            with transaction.atomic():
                mov_personal = Movimiento.objects.create(
                    tipo=tipo, nombre=nombre, detalle=detalle,
                    monto=monto, concepto=concepto, usuario=request.user,
                    grupo=None, fecha_hora=timezone.now(), tarjeta=tarjeta,
                    cuotas=cuotas,
                )

                if tarjeta and tarjeta.tipo == Tarjeta.TIPO_CREDITO and tipo == Movimiento.TIPO_GASTO:
                    tarjeta.cupo_usado = (tarjeta.cupo_usado or 0) + monto
                    tarjeta.save(update_fields=['cupo_usado'])

                if registrar_en_grupo and grupo_id:
                    if not GrupoMiembro.objects.filter(
                        usuario=request.user, grupo_id=grupo_id, grupo__activo=True
                    ).exists():
                        raise ValueError('No eres miembro del grupo seleccionado.')

                    grupo = Grupo.objects.get(id=grupo_id, activo=True)

                    concepto_grupal = None
                    if concepto:
                        concepto_grupal, _ = Concepto.objects.get_or_create(
                            grupo=grupo, nombre=concepto.nombre, tipo=concepto.tipo,
                            defaults={'activo': True, 'usuario': None},
                        )

                    mov_grupo = Movimiento.objects.create(
                        tipo=tipo, nombre=nombre, detalle=detalle,
                        monto=monto, concepto=concepto_grupal, usuario=request.user,
                        grupo=grupo, fecha_hora=mov_personal.fecha_hora,
                    )
                    ReplicaGrupal.objects.create(
                        movimiento_personal=mov_personal,
                        movimiento_grupo=mov_grupo,
                        grupo=grupo,
                    )

                    tipo_notif = Notificacion.TIPO_GASTO if tipo == 'Gasto' else Notificacion.TIPO_INGRESO
                    concepto_nombre = concepto_grupal.nombre if concepto_grupal else (concepto.nombre if concepto else 'sin concepto')
                    titulo = (
                        f'Se {"generó un gasto" if tipo == "Gasto" else "registró un ingreso"} '
                        f'por ${monto:,} de {request.user.username} por {concepto_nombre}'
                    ).replace(',', '.')
                    crear_notificaciones_grupo(grupo, tipo_notif, titulo, referencia_id=mov_grupo.id, excluir_usuario=request.user)

                    if es_compartido and tipo == 'Gasto' and usuario_deudor_id:
                        monto_pendiente = int(monto_compartido_str) if monto_compartido_str.isdigit() else monto
                        monto_pendiente = max(1, min(monto_pendiente, monto - 1))
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
                        grupo_doc = grupo

            logger.info('MovimientoWeb creado id=%s tipo=%s monto=%s grupo=%s compartido=%s user=%s', mov_personal.id, tipo, monto, grupo_id or None, es_compartido, request.user.id)
            messages.success(request, f'{tipo} registrado exitosamente.')

            if comprobante and grupo_doc:
                ext = os.path.splitext(comprobante.name)[1].lstrip('.').lower()
                nombre_doc = f"{nombre} - {mov_personal.fecha_hora.strftime('%d/%m/%Y')}"
                Documento.objects.create(
                    nombre=nombre_doc[:255],
                    archivo=comprobante,
                    tipo_archivo=ext,
                    tamano_bytes=comprobante.size,
                    usuario=request.user,
                    grupo=grupo_doc,
                )
        except GrupoMiembro.DoesNotExist:
            logger.warning('MovimientoWeb: deudor %s no pertenece al grupo=%s user=%s', usuario_deudor_id, grupo_id, request.user.id)
            messages.error(request, 'El usuario seleccionado no pertenece al grupo.')
        except Exception as e:
            logger.error('Error creando movimiento web user=%s: %s', request.user.id, e, exc_info=True)
            messages.error(request, f'Error al registrar: {e}')

    return redirect('finances-dashboard')


@login_required
def gastos_compartidos_view(request):
    grupos_ids = _get_grupos_usuario(request.user).values_list('grupo_id', flat=True)

    if request.method == 'POST':
        gasto_id = request.POST.get('gasto_id')
        try:
            gasto = GastoCompartido.objects.get(
                id=gasto_id, usuario_acreedor=request.user,
                grupo_id__in=grupos_ids, pagado=False
            )
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
                    nombre='Cobro de deuda',
                    usuario=request.user,
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
                    nombre='Pago de deuda',
                    usuario=gasto.usuario_deudor,
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
            logger.info('GastoCompartidoWeb %s marcado pagado monto=%s user=%s', gasto_id, gasto.monto_pendiente, request.user.id)
            messages.success(request, 'Gasto marcado como pagado.')
        except GastoCompartido.DoesNotExist:
            logger.warning('GastoCompartidoWeb %s no encontrado user=%s', gasto_id, request.user.id)
            messages.error(request, 'No se pudo marcar como pagado.')
        return redirect('finances-shared')

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

    usuarios_con_deudas = {}
    for g in pendientes_pago:
        uid = str(g.usuario_acreedor_id)
        if uid not in usuarios_con_deudas:
            usuarios_con_deudas[uid] = {'id': uid, 'username': g.usuario_acreedor.username, 'debo': 0, 'me_deben': 0, 'count': 0}
        usuarios_con_deudas[uid]['debo'] += g.monto_pendiente
        usuarios_con_deudas[uid]['count'] += 1
    for g in pendientes_cobro:
        uid = str(g.usuario_deudor_id)
        if uid not in usuarios_con_deudas:
            usuarios_con_deudas[uid] = {'id': uid, 'username': g.usuario_deudor.username, 'debo': 0, 'me_deben': 0, 'count': 0}
        usuarios_con_deudas[uid]['me_deben'] += g.monto_pendiente
        usuarios_con_deudas[uid]['count'] += 1

    usuarios_liquidables = [u for u in usuarios_con_deudas.values() if u['count'] > 1]

    return render(request, 'finances/shared_expenses.html', {
        'pendientes_pago': pendientes_pago,
        'pendientes_cobro': pendientes_cobro,
        'total_debo': total_debo,
        'total_me_deben': total_me_deben,
        'usuarios_con_deudas_json': json.dumps(usuarios_liquidables),
    })


@login_required
def liquidar_view(request):
    if request.method != 'POST':
        return redirect('finances-shared')

    otro_usuario_id = request.POST.get('otro_usuario_id', '').strip()
    logger.debug('LiquidarWeb user=%s otro_usuario=%s', request.user.id, otro_usuario_id)
    try:
        otro_usuario = User.objects.get(id=otro_usuario_id)
    except (User.DoesNotExist, ValueError):
        logger.warning('LiquidarWeb usuario %s no encontrado user=%s', otro_usuario_id, request.user.id)
        messages.error(request, 'Usuario no encontrado.')
        return redirect('finances-shared')

    grupos_ids = list(_get_grupos_usuario(request.user).values_list('grupo_id', flat=True))

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
        logger.warning('LiquidarWeb: sin deudas pendientes entre user=%s y user=%s', request.user.id, otro_usuario_id)
        messages.warning(request, f'No hay deudas pendientes con {otro_usuario.username}.')
        return redirect('finances-shared')

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

    logger.info('LiquidarWeb completado user=%s otro=%s neto=%s', request.user.id, otro_usuario_id, neto)
    if neto == 0:
        messages.success(request, f'¡Liquidado! Tú y {otro_usuario.username} quedan a mano.')
    elif neto > 0:
        messages.success(request, f'Liquidado. {otro_usuario.username} te debe ${abs(neto):,} neto.'.replace(',', '.'))
    else:
        messages.success(request, f'Liquidado. Le debes ${abs(neto):,} neto a {otro_usuario.username}.'.replace(',', '.'))
    return redirect('finances-shared')


@login_required
def group_finances_list_view(request):
    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    memberships = _get_grupos_usuario(request.user)
    grupos_data = []
    for m in memberships:
        gasto_mes = (
            Movimiento.objects
            .filter(grupo=m.grupo, tipo='Gasto',
                    fecha_hora__date__gte=mes_inicio, fecha_hora__date__lte=hoy)
            .aggregate(t=Sum('monto'))['t'] or 0
        )
        ingreso_mes = (
            Movimiento.objects
            .filter(grupo=m.grupo, tipo='Ingreso',
                    fecha_hora__date__gte=mes_inicio, fecha_hora__date__lte=hoy)
            .aggregate(t=Sum('monto'))['t'] or 0
        )
        miembros_count = GrupoMiembro.objects.filter(grupo=m.grupo).count()
        grupos_data.append({
            'grupo': m.grupo,
            'gasto_mes': gasto_mes,
            'ingreso_mes': ingreso_mes,
            'saldo_mes': ingreso_mes - gasto_mes,
            'miembros_count': miembros_count,
            'rol': m.rol,
        })
    return render(request, 'finances/group_finances_list.html', {
        'grupos_data': grupos_data,
    })


@login_required
def group_finances_view(request, group_id):
    grupo = get_object_or_404(Grupo, id=group_id, activo=True)
    if not GrupoMiembro.objects.filter(usuario=request.user, grupo=grupo).exists():
        messages.error(request, 'No tienes acceso a este grupo.')
        return redirect('finances-group-list')

    hoy = date.today()
    mes_inicio = hoy.replace(day=1)

    movimientos_qs = Movimiento.objects.filter(grupo=grupo)
    movimientos_mes = movimientos_qs.filter(
        fecha_hora__date__gte=mes_inicio, fecha_hora__date__lte=hoy,
    )

    gasto_total = movimientos_qs.filter(tipo='Gasto').aggregate(t=Sum('monto'))['t'] or 0
    ingreso_total = movimientos_qs.filter(tipo='Ingreso').aggregate(t=Sum('monto'))['t'] or 0
    gasto_mes = movimientos_mes.filter(tipo='Gasto').aggregate(t=Sum('monto'))['t'] or 0
    ingreso_mes = movimientos_mes.filter(tipo='Ingreso').aggregate(t=Sum('monto'))['t'] or 0
    saldo_mes = ingreso_mes - gasto_mes

    ultimos = (
        movimientos_qs
        .select_related('concepto', 'usuario')
        .order_by('-fecha_hora')[:10]
    )

    miembros = (
        GrupoMiembro.objects
        .filter(grupo=grupo)
        .select_related('usuario')
        .order_by('usuario__username')
    )

    # Presupuestos del grupo con divisiones para este usuario
    presupuestos = (
        RegistroPresupuesto.objects
        .filter(grupo=grupo)
        .select_related('concepto')
        .prefetch_related('divisiones__usuario')
        .order_by('-tipo', '-monto')
    )
    mis_divisiones = (
        DivisionPresupuesto.objects
        .filter(grupo=grupo, usuario=request.user)
        .select_related('registro_presupuesto__concepto')
        .order_by('-registro_presupuesto__monto')
    )
    total_presupuesto_gasto = sum(
        p.monto for p in presupuestos if p.tipo == 'Gasto'
    )
    total_presupuesto_ingreso = sum(
        p.monto for p in presupuestos if p.tipo == 'Ingreso'
    )

    # Gastos compartidos pendientes del grupo para el usuario actual
    pendientes_pago = (
        GastoCompartido.objects
        .filter(usuario_deudor=request.user, grupo=grupo, pagado=False)
        .select_related('movimiento__concepto', 'usuario_acreedor')
    )
    pendientes_cobro = (
        GastoCompartido.objects
        .filter(usuario_acreedor=request.user, grupo=grupo, pagado=False)
        .select_related('movimiento__concepto', 'usuario_deudor')
    )
    total_debo = pendientes_pago.aggregate(t=Sum('monto_pendiente'))['t'] or 0
    total_me_deben = pendientes_cobro.aggregate(t=Sum('monto_pendiente'))['t'] or 0

    return render(request, 'finances/group_finances.html', {
        'grupo': grupo,
        'gasto_total': gasto_total,
        'ingreso_total': ingreso_total,
        'gasto_mes': gasto_mes,
        'ingreso_mes': ingreso_mes,
        'saldo_mes': saldo_mes,
        'ultimos_movimientos': ultimos,
        'miembros': miembros,
        'presupuestos': presupuestos,
        'mis_divisiones': mis_divisiones,
        'total_presupuesto_gasto': total_presupuesto_gasto,
        'total_presupuesto_ingreso': total_presupuesto_ingreso,
        'pendientes_pago': pendientes_pago,
        'pendientes_cobro': pendientes_cobro,
        'total_debo': total_debo,
        'total_me_deben': total_me_deben,
    })


# ── Asistente de división de gastos ─────────────────────────────────────────

@login_required
def split_assistant_view(request):
    memberships = _get_grupos_usuario(request.user)
    if not memberships.exists():
        messages.info(request, 'Para usar el asistente necesitas pertenecer a un grupo.')
        return redirect('group-manage')

    grupos_data = []
    for m in memberships:
        miembros = GrupoMiembro.objects.filter(grupo=m.grupo).select_related('usuario')
        grupos_data.append({
            'id': str(m.grupo_id),
            'nombre': m.grupo.nombre,
            'miembros': [
                {'id': str(gm.usuario_id), 'username': gm.usuario.username}
                for gm in miembros
            ],
        })

    return render(request, 'finances/split.html', {
        'grupos_json': json.dumps(grupos_data),
        'current_user_id': str(request.user.id),
        'current_username': request.user.username,
    })


@login_required
def split_confirm_view(request):
    if request.method != 'POST':
        from django.http import JsonResponse
        return JsonResponse({'error': 'Método no permitido.'}, status=405)

    from django.http import JsonResponse

    try:
        data = json.loads(request.body)
        grupo_id = data['grupo_id']
        monto_total = int(data['monto_total'])
        concepto_nombre = (data.get('concepto_nombre') or 'División de cuenta').strip()
        distribuciones = data['distribuciones']

        grupo = get_object_or_404(Grupo, id=grupo_id, activo=True)
        if not GrupoMiembro.objects.filter(usuario=request.user, grupo=grupo).exists():
            return JsonResponse({'error': 'No perteneces a este grupo.'}, status=403)

        if monto_total <= 0:
            return JsonResponse({'error': 'El monto total debe ser mayor a cero.'}, status=400)

        payer_id = str(data.get('payer_id') or request.user.id)
        try:
            payer = User.objects.get(id=payer_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'El pagador seleccionado no existe.'}, status=400)
        if not GrupoMiembro.objects.filter(usuario=payer, grupo=grupo).exists():
            return JsonResponse({'error': 'El pagador no es miembro del grupo.'}, status=400)

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
                monto=monto_total,
                concepto=concepto_personal,
                usuario=payer, grupo=None,
                fecha_hora=timezone.now(),
            )
            mov = Movimiento.objects.create(
                tipo='Gasto', nombre=concepto_nombre,
                detalle='Asistente de división de gastos',
                monto=monto_total, concepto=concepto_grupo,
                usuario=payer, grupo=grupo,
                fecha_hora=timezone.now(),
            )
            gastos_creados = []
            for d in distribuciones:
                if str(d['usuario_id']) == str(payer.id):
                    continue
                monto_deudor = int(d['monto'])
                if monto_deudor <= 0:
                    continue
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
                gastos_creados.append({'username': d.get('username', ''), 'monto': monto_deudor})

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

        return JsonResponse({'ok': True, 'gastos': gastos_creados})

    except (KeyError, ValueError, json.JSONDecodeError) as e:
        return JsonResponse({'error': f'Datos inválidos: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── Ahorros personales ───────────────────────────────────────────────────────

def _parse_monto_ahorro(raw):
    return int(str(raw).replace('.', '').replace(',', ''))


def _get_or_create_concepto_ahorro(user, tipo):
    """Devuelve el concepto personal de ahorro para el usuario (Gasto o Ingreso)."""
    nombre = 'Ahorro' if tipo == Concepto.TIPO_GASTO else 'Retiro de ahorro'
    concepto, _ = Concepto.objects.get_or_create(
        nombre=nombre,
        usuario=user,
        defaults={'tipo': tipo, 'activo': True, 'grupo': None},
    )
    return concepto


def _savings_hito_msg(pct):
    if pct >= 100:
        return 'completada'
    if pct >= 75:
        return 'setenta_y_cinco'
    if pct >= 50:
        return 'cincuenta'
    return None


def _build_metas_data(metas_qs):
    hoy = date.today()
    result = []
    for m in metas_qs:
        ahorrado = m.ahorrado or 0
        pct = min(100, round(ahorrado / m.monto_objetivo * 100)) if m.monto_objetivo else 0
        dias = (m.fecha_limite - hoy).days if m.fecha_limite else None
        result.append({
            'meta': m,
            'ahorrado': ahorrado,
            'pct': pct,
            'dias': dias,
            'completada': ahorrado >= m.monto_objetivo,
        })
    return result


@login_required
def savings_personal_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        fecha_limite_str = request.POST.get('fecha_limite', '').strip()
        try:
            monto_objetivo = _parse_monto_ahorro(request.POST.get('monto_objetivo', '0'))
            assert monto_objetivo > 0 and nombre
            fecha_limite = date.fromisoformat(fecha_limite_str) if fecha_limite_str else None
            meta_obj = MetaAhorro.objects.create(
                nombre=nombre,
                monto_objetivo=monto_objetivo,
                fecha_limite=fecha_limite,
                tipo=MetaAhorro.TIPO_PERSONAL,
                usuario=request.user,
                grupo=None,
            )
            logger.info('MetaAhorroWeb personal creada id=%s nombre=%s user=%s', meta_obj.id, nombre, request.user.id)
            messages.success(request, f'Meta "{nombre}" creada.')
        except (ValueError, AssertionError) as e:
            logger.warning('MetaAhorroWeb datos inválidos nombre=%s user=%s: %s', nombre, request.user.id, e)
            messages.error(request, 'Datos inválidos.')
        return redirect('finances-savings-personal')

    metas = (
        MetaAhorro.objects
        .filter(usuario=request.user, tipo=MetaAhorro.TIPO_PERSONAL, activa=True)
        .annotate(ahorrado=Sum('aportes__monto'))
        .order_by('fecha_limite', 'created_at')
    )
    return render(request, 'finances/savings_personal.html', {
        'metas_data': _build_metas_data(metas),
    })


@login_required
def savings_personal_detail_view(request, meta_id):
    meta = get_object_or_404(
        MetaAhorro, id=meta_id, usuario=request.user, tipo=MetaAhorro.TIPO_PERSONAL
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'aportar':
            try:
                monto = _parse_monto_ahorro(request.POST.get('monto', '0'))
                assert monto > 0
                with transaction.atomic():
                    concepto = _get_or_create_concepto_ahorro(request.user, Concepto.TIPO_GASTO)
                    mov = Movimiento.objects.create(
                        tipo=Movimiento.TIPO_GASTO,
                        nombre=f'Ahorro: {meta.nombre}',
                        detalle='Aporte a meta de ahorro',
                        monto=monto,
                        concepto=concepto,
                        usuario=request.user,
                        grupo=None,
                        fecha_hora=timezone.now(),
                    )
                    AporteAhorro.objects.create(
                        meta=meta, usuario=request.user,
                        monto=monto, fecha=timezone.now(), movimiento=mov,
                    )
                    ahorrado = meta.aportes.aggregate(t=Sum('monto'))['t'] or 0
                    pct = ahorrado / meta.monto_objetivo * 100 if meta.monto_objetivo else 0
                    hito = _savings_hito_msg(pct)
                    if hito == 'completada':
                        messages.success(request, f'¡Completaste tu meta "{meta.nombre}"! 🎉')
                    elif hito == 'setenta_y_cinco':
                        messages.success(request, f'¡Vas al 75% de "{meta.nombre}"!')
                    elif hito == 'cincuenta':
                        messages.success(request, f'¡Llegaste al 50% de "{meta.nombre}"!')
                    else:
                        messages.success(request, 'Aporte registrado.')
                    logger.info('AporteAhorroWeb meta=%s monto=%s user=%s pct=%.1f', meta_id, monto, request.user.id, pct)
            except (ValueError, AssertionError) as e:
                logger.warning('AporteAhorroWeb monto inválido meta=%s user=%s: %s', meta_id, request.user.id, e)
                messages.error(request, 'Monto inválido.')

        elif action == 'retirar':
            try:
                monto = _parse_monto_ahorro(request.POST.get('monto', '0'))
                ahorrado = meta.aportes.aggregate(t=Sum('monto'))['t'] or 0
                assert 0 < monto <= ahorrado
                with transaction.atomic():
                    concepto = _get_or_create_concepto_ahorro(request.user, Concepto.TIPO_INGRESO)
                    mov = Movimiento.objects.create(
                        tipo=Movimiento.TIPO_INGRESO,
                        nombre=f'Retiro de ahorro: {meta.nombre}',
                        detalle='Retiro de meta de ahorro',
                        monto=monto,
                        concepto=concepto,
                        usuario=request.user,
                        grupo=None,
                        fecha_hora=timezone.now(),
                    )
                    AporteAhorro.objects.create(
                        meta=meta, usuario=request.user,
                        monto=-monto, fecha=timezone.now(), movimiento=mov,
                    )
                logger.info('RetiroAhorroWeb meta=%s monto=%s user=%s', meta_id, monto, request.user.id)
                messages.success(request, 'Retiro registrado.')
            except (ValueError, AssertionError) as e:
                logger.warning('RetiroAhorroWeb monto inválido meta=%s user=%s: %s', meta_id, request.user.id, e)
                messages.error(request, 'Monto de retiro inválido.')

        elif action == 'editar':
            nombre = request.POST.get('nombre', '').strip()
            fecha_limite_str = request.POST.get('fecha_limite', '').strip()
            try:
                monto_objetivo = _parse_monto_ahorro(request.POST.get('monto_objetivo', '0'))
                assert monto_objetivo > 0 and nombre
                meta.nombre = nombre
                meta.monto_objetivo = monto_objetivo
                meta.fecha_limite = date.fromisoformat(fecha_limite_str) if fecha_limite_str else None
                meta.save()
                messages.success(request, 'Meta actualizada.')
            except (ValueError, AssertionError):
                messages.error(request, 'Datos inválidos.')

        elif action == 'archivar':
            meta.activa = False
            meta.save()
            messages.success(request, f'Meta "{meta.nombre}" archivada.')
            return redirect('finances-savings-personal')

        return redirect('finances-savings-personal-detail', meta_id=meta_id)

    aportes = meta.aportes.select_related('usuario').order_by('-fecha')
    ahorrado = aportes.aggregate(t=Sum('monto'))['t'] or 0
    pct = min(100, round(ahorrado / meta.monto_objetivo * 100)) if meta.monto_objetivo else 0
    dias = (meta.fecha_limite - date.today()).days if meta.fecha_limite else None

    return render(request, 'finances/savings_personal_detail.html', {
        'meta': meta,
        'aportes': aportes,
        'ahorrado': ahorrado,
        'pct': pct,
        'dias': dias,
        'completada': ahorrado >= meta.monto_objetivo,
    })


# ── Ahorros grupales ─────────────────────────────────────────────────────────

@login_required
def savings_group_view(request, group_id):
    grupo = get_object_or_404(Grupo, id=group_id, activo=True)
    get_object_or_404(GrupoMiembro, usuario=request.user, grupo=grupo)
    es_admin = GrupoMiembro.objects.filter(
        usuario=request.user, grupo=grupo, rol=GrupoMiembro.ROL_ADMIN
    ).exists()

    if request.method == 'POST':
        if not es_admin:
            logger.warning('MetaAhorroGrupalWeb: user=%s no es admin del grupo=%s', request.user.id, group_id)
            messages.error(request, 'Solo el admin puede crear metas grupales.')
            return redirect('finances-savings-group', group_id=group_id)

        nombre = request.POST.get('nombre', '').strip()
        fecha_limite_str = request.POST.get('fecha_limite', '').strip()
        notificar = request.POST.get('notificar') == '1'
        try:
            monto_objetivo = _parse_monto_ahorro(request.POST.get('monto_objetivo', '0'))
            assert monto_objetivo > 0 and nombre
            fecha_limite = date.fromisoformat(fecha_limite_str) if fecha_limite_str else None
            meta = MetaAhorro.objects.create(
                nombre=nombre,
                monto_objetivo=monto_objetivo,
                fecha_limite=fecha_limite,
                tipo=MetaAhorro.TIPO_GRUPAL,
                usuario=None,
                grupo=grupo,
            )
            if notificar:
                crear_notificaciones_grupo(
                    grupo, Notificacion.TIPO_GASTO,
                    f'{request.user.username} creó la meta de ahorro grupal "{nombre}".',
                    referencia_id=meta.id,
                    excluir_usuario=request.user,
                )
            logger.info('MetaAhorroGrupalWeb creada id=%s nombre=%s grupo=%s user=%s', meta.id, nombre, group_id, request.user.id)
            messages.success(request, f'Meta grupal "{nombre}" creada.')
        except (ValueError, AssertionError) as e:
            logger.warning('MetaAhorroGrupalWeb datos inválidos grupo=%s user=%s: %s', group_id, request.user.id, e)
            messages.error(request, 'Datos inválidos.')
        return redirect('finances-savings-group', group_id=group_id)

    metas = (
        MetaAhorro.objects
        .filter(grupo=grupo, tipo=MetaAhorro.TIPO_GRUPAL, activa=True)
        .annotate(ahorrado=Sum('aportes__monto'))
        .order_by('fecha_limite', 'created_at')
    )
    return render(request, 'finances/savings_group.html', {
        'grupo': grupo,
        'metas_data': _build_metas_data(metas),
        'es_admin': es_admin,
    })


@login_required
def savings_group_detail_view(request, group_id, meta_id):
    grupo = get_object_or_404(Grupo, id=group_id, activo=True)
    get_object_or_404(GrupoMiembro, usuario=request.user, grupo=grupo)
    es_admin = GrupoMiembro.objects.filter(
        usuario=request.user, grupo=grupo, rol=GrupoMiembro.ROL_ADMIN
    ).exists()
    meta = get_object_or_404(MetaAhorro, id=meta_id, grupo=grupo, tipo=MetaAhorro.TIPO_GRUPAL)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'aportar':
            try:
                monto = _parse_monto_ahorro(request.POST.get('monto', '0'))
                assert monto > 0
                with transaction.atomic():
                    concepto = _get_or_create_concepto_ahorro(request.user, Concepto.TIPO_GASTO)
                    mov = Movimiento.objects.create(
                        tipo=Movimiento.TIPO_GASTO,
                        nombre=f'Ahorro grupal: {meta.nombre}',
                        detalle=f'Aporte a meta de ahorro del grupo {grupo.nombre}',
                        monto=monto,
                        concepto=concepto,
                        usuario=request.user,
                        grupo=None,
                        fecha_hora=timezone.now(),
                    )
                    AporteAhorro.objects.create(
                        meta=meta, usuario=request.user,
                        monto=monto, fecha=timezone.now(), movimiento=mov,
                    )
                    ahorrado = meta.aportes.aggregate(t=Sum('monto'))['t'] or 0
                    pct = ahorrado / meta.monto_objetivo * 100 if meta.monto_objetivo else 0
                    hito = _savings_hito_msg(pct)
                    if hito == 'completada':
                        crear_notificaciones_grupo(
                            grupo, Notificacion.TIPO_GASTO,
                            f'¡La meta de ahorro "{meta.nombre}" fue completada!',
                            referencia_id=meta.id,
                        )
                        messages.success(request, f'¡Meta "{meta.nombre}" completada! 🎉')
                    elif hito == 'setenta_y_cinco':
                        messages.success(request, f'¡El grupo va al 75% de "{meta.nombre}"!')
                    elif hito == 'cincuenta':
                        messages.success(request, f'¡El grupo llegó al 50% de "{meta.nombre}"!')
                    else:
                        messages.success(request, 'Aporte registrado.')
            except (ValueError, AssertionError):
                messages.error(request, 'Monto inválido.')

        elif action == 'archivar' and es_admin:
            meta.activa = False
            meta.save()
            messages.success(request, f'Meta "{meta.nombre}" archivada.')
            return redirect('finances-savings-group', group_id=group_id)

        elif action == 'editar' and es_admin:
            nombre = request.POST.get('nombre', '').strip()
            fecha_limite_str = request.POST.get('fecha_limite', '').strip()
            try:
                monto_objetivo = _parse_monto_ahorro(request.POST.get('monto_objetivo', '0'))
                assert monto_objetivo > 0 and nombre
                meta.nombre = nombre
                meta.monto_objetivo = monto_objetivo
                meta.fecha_limite = date.fromisoformat(fecha_limite_str) if fecha_limite_str else None
                meta.save()
                messages.success(request, 'Meta actualizada.')
            except (ValueError, AssertionError):
                messages.error(request, 'Datos inválidos.')

        return redirect('finances-savings-group-detail', group_id=group_id, meta_id=meta_id)

    aportes = meta.aportes.select_related('usuario').order_by('-fecha')
    ahorrado = aportes.aggregate(t=Sum('monto'))['t'] or 0
    pct = min(100, round(ahorrado / meta.monto_objetivo * 100)) if meta.monto_objetivo else 0
    dias = (meta.fecha_limite - date.today()).days if meta.fecha_limite else None

    miembros = GrupoMiembro.objects.filter(grupo=grupo).select_related('usuario')
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

    return render(request, 'finances/savings_group_detail.html', {
        'grupo': grupo,
        'meta': meta,
        'aportes': aportes,
        'ahorrado': ahorrado,
        'pct': pct,
        'dias': dias,
        'completada': ahorrado >= meta.monto_objetivo,
        'es_admin': es_admin,
        'desglose': desglose,
    })


# ── Tarjetas ─────────────────────────────────────────────────────────────────

@login_required
def tarjetas_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            nombre = request.POST.get('nombre', '').strip()
            tipo = request.POST.get('tipo', '')
            banco = request.POST.get('banco', '').strip()
            cupo_total_str = request.POST.get('cupo_total', '').replace('.', '').replace(',', '').strip()
            cupo_usado_str = request.POST.get('cupo_usado', '').replace('.', '').replace(',', '').strip()

            if not nombre or tipo not in ('Debito', 'Credito') or not banco:
                logger.warning('TarjetaWeb datos inválidos nombre=%s tipo=%s user=%s', nombre, tipo, request.user.id)
                messages.error(request, 'Nombre, tipo y banco son obligatorios.')
            else:
                cupo_total = int(cupo_total_str) if cupo_total_str.isdigit() and tipo == 'Credito' else None
                cupo_usado = int(cupo_usado_str) if cupo_usado_str.isdigit() and tipo == 'Credito' else None
                if cupo_total is not None and cupo_usado is not None and cupo_usado > cupo_total:
                    logger.warning('TarjetaWeb cupo_usado>cupo_total nombre=%s user=%s', nombre, request.user.id)
                    messages.error(request, 'El cupo utilizado no puede ser mayor al cupo total.')
                else:
                    t = Tarjeta.objects.create(
                        nombre=nombre, tipo=tipo, banco=banco,
                        cupo_total=cupo_total, cupo_usado=cupo_usado,
                        usuario=request.user,
                    )
                    logger.info('TarjetaWeb creada id=%s nombre=%s tipo=%s user=%s', t.id, nombre, tipo, request.user.id)
                    messages.success(request, f'Tarjeta "{nombre}" agregada.')

        elif action == 'delete':
            tarjeta_id = request.POST.get('tarjeta_id')
            try:
                t = Tarjeta.objects.get(id=tarjeta_id, usuario=request.user, activa=True)
                t.activa = False
                t.save()
                logger.info('TarjetaWeb eliminada id=%s user=%s', tarjeta_id, request.user.id)
                messages.success(request, 'Tarjeta eliminada.')
            except Tarjeta.DoesNotExist:
                logger.warning('TarjetaWeb %s no encontrada user=%s', tarjeta_id, request.user.id)
                messages.error(request, 'Tarjeta no encontrada.')

        return redirect('finances-tarjetas')

    tarjetas = list(Tarjeta.objects.filter(usuario=request.user, activa=True).order_by('-created_at'))
    for t in tarjetas:
        if t.tipo == Tarjeta.TIPO_DEBITO:
            ingresos = Movimiento.objects.filter(tarjeta=t, tipo=Movimiento.TIPO_INGRESO).aggregate(s=Sum('monto'))['s'] or 0
            gastos = Movimiento.objects.filter(tarjeta=t, tipo=Movimiento.TIPO_GASTO).aggregate(s=Sum('monto'))['s'] or 0
            t.saldo_disponible = ingresos - gastos
        else:
            t.saldo_disponible = None
    return render(request, 'finances/tarjetas.html', {
        'tarjetas': tarjetas,
        'bancos': BANCOS_CHILE,
    })


@login_required
def tarjeta_detail_view(request, tarjeta_id):
    tarjeta = get_object_or_404(Tarjeta, id=tarjeta_id, usuario=request.user, activa=True)
    movimientos = (
        Movimiento.objects
        .filter(tarjeta=tarjeta)
        .select_related('concepto')
        .order_by('-fecha_hora')
    )
    total_gastos = movimientos.filter(tipo='Gasto').aggregate(t=Sum('monto'))['t'] or 0
    total_ingresos = movimientos.filter(tipo='Ingreso').aggregate(t=Sum('monto'))['t'] or 0
    return render(request, 'finances/tarjeta_detail.html', {
        'tarjeta': tarjeta,
        'movimientos': movimientos,
        'total_gastos': total_gastos,
        'total_ingresos': total_ingresos,
    })
