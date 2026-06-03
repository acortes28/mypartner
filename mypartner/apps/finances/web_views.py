import csv
import io
import json
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

from .models import (
    Concepto, DivisionPresupuesto, GastoCompartido,
    Movimiento, RegistroPresupuesto, ReplicaGrupal,
)

User = get_user_model()


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

    gasto_total = movimientos_qs.filter(tipo='Gasto').aggregate(t=Sum('monto'))['t'] or 0
    ingreso_total = movimientos_qs.filter(tipo='Ingreso').aggregate(t=Sum('monto'))['t'] or 0
    saldo_restante = ingreso_total - gasto_total
    desviacion = presupuesto_acum - gasto_total

    gastos_concepto = (
        movimientos_qs.filter(tipo='Gasto')
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

                messages.success(request, 'Registro de presupuesto agregado.')
            except Exception as e:
                messages.error(request, f'Error al agregar registro: {e}')

        elif action == 'modify':
            registro_id = request.POST.get('registro_id')
            monto_str = request.POST.get('monto', '0').replace('.', '').replace(',', '')
            try:
                registro = RegistroPresupuesto.objects.get(id=registro_id, usuario=request.user)
                registro.monto = int(monto_str)
                registro.save()
                messages.success(request, 'Monto actualizado.')
            except Exception:
                messages.error(request, 'Error al modificar.')

        elif action == 'delete':
            registro_id = request.POST.get('registro_id')
            try:
                registro = RegistroPresupuesto.objects.get(id=registro_id, usuario=request.user)
                registro.delete()
                messages.success(request, 'Registro eliminado.')
            except Exception:
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
        Q(periodicidad='Mensual') |
        Q(periodicidad='Anual', fecha__month=mes) |
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
                    messages.error(request, f'Ya existe un concepto llamado "{nombre}".')
                else:
                    Concepto.objects.create(nombre=nombre, tipo=tipo, usuario=request.user, grupo=None)
                    messages.success(request, 'Concepto agregado.')
            else:
                messages.error(request, 'Nombre y tipo son obligatorios.')

        elif action == 'edit':
            concepto_id = request.POST.get('concepto_id')
            nombre = request.POST.get('nombre', '').strip()
            try:
                c = Concepto.objects.get(id=concepto_id, usuario=request.user, activo=True)
                if Concepto.objects.filter(usuario=request.user, nombre__iexact=nombre, activo=True).exclude(id=concepto_id).exists():
                    messages.error(request, f'Ya existe un concepto llamado "{nombre}".')
                    return redirect('finances-concepts')
                c.nombre = nombre
                c.save()
                messages.success(request, 'Concepto actualizado.')
            except Concepto.DoesNotExist:
                messages.error(request, 'Concepto no encontrado.')

        elif action == 'delete':
            concepto_id = request.POST.get('concepto_id')
            opcion = request.POST.get('opcion', '')
            try:
                c = Concepto.objects.get(id=concepto_id, usuario=request.user, activo=True)
                if opcion == 'eliminar_movimientos':
                    Movimiento.objects.filter(concepto=c).delete()
                    c.activo = False
                    c.save()
                    messages.success(request, 'Concepto y movimientos eliminados.')
                elif opcion == 'mantener_movimientos':
                    Movimiento.objects.filter(concepto=c).update(concepto=None)
                    c.activo = False
                    c.save()
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
                    messages.success(request, 'Concepto eliminado.')
            except Concepto.DoesNotExist:
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

        try:
            monto = int(monto_str)
            assert monto > 0 and nombre

            concepto = None
            if concepto_id:
                try:
                    concepto = Concepto.objects.get(id=concepto_id, usuario=request.user, activo=True)
                except Concepto.DoesNotExist:
                    pass

            with transaction.atomic():
                mov_personal = Movimiento.objects.create(
                    tipo=tipo, nombre=nombre, detalle=detalle,
                    monto=monto, concepto=concepto, usuario=request.user,
                    grupo=None, fecha_hora=timezone.now(),
                )

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

            messages.success(request, f'{tipo} registrado exitosamente.')
        except GrupoMiembro.DoesNotExist:
            messages.error(request, 'El usuario seleccionado no pertenece al grupo.')
        except Exception as e:
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
            gasto.pagado = True
            gasto.save()
            concepto_nombre = gasto.movimiento.concepto.nombre if gasto.movimiento.concepto else 'sin concepto'
            Notificacion.objects.create(
                titulo=f'{request.user.username} marcó como pagado el gasto compartido de ${gasto.monto_pendiente:,} por {concepto_nombre}.'.replace(',', '.'),
                tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                referencia_id=gasto.movimiento_id,
                usuario=gasto.usuario_deudor,
            )
            messages.success(request, 'Gasto marcado como pagado.')
        except GastoCompartido.DoesNotExist:
            messages.error(request, 'No se pudo marcar como pagado.')
        return redirect('finances-shared')

    pendientes_pago = (
        GastoCompartido.objects
        .filter(usuario_deudor=request.user, grupo_id__in=grupos_ids, pagado=False)
        .select_related('movimiento__concepto', 'usuario_acreedor', 'grupo')
        .order_by('-created_at')
    )
    pendientes_cobro = (
        GastoCompartido.objects
        .filter(usuario_acreedor=request.user, grupo_id__in=grupos_ids, pagado=False)
        .select_related('movimiento__concepto', 'usuario_deudor', 'grupo')
        .order_by('-created_at')
    )
    total_debo = pendientes_pago.aggregate(t=Sum('monto_pendiente'))['t'] or 0
    total_me_deben = pendientes_cobro.aggregate(t=Sum('monto_pendiente'))['t'] or 0

    return render(request, 'finances/shared_expenses.html', {
        'pendientes_pago': pendientes_pago,
        'pendientes_cobro': pendientes_cobro,
        'total_debo': total_debo,
        'total_me_deben': total_me_deben,
    })


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
