import csv
import io
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from apps.groups.models import GrupoMiembro
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from django.contrib.auth import get_user_model

from .models import Concepto, GastoCompartido, Movimiento, RegistroPresupuesto


def _get_grupo(user):
    m = GrupoMiembro.objects.filter(usuario=user, grupo__activo=True).select_related('grupo').first()
    return m.grupo if m else None


def _require_group(request):
    grupo = _get_grupo(request.user)
    if not grupo:
        messages.info(request, 'Para acceder a este módulo necesitas pertenecer a un grupo.')
        return None, redirect('group-manage')
    return grupo, None


@login_required
def dashboard_view(request):
    grupo, redir = _require_group(request)
    if redir:
        return redir

    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    vista = request.GET.get('vista', 'historico')
    if vista not in ('mensual', 'historico'):
        vista = 'historico'

    movimientos_qs = Movimiento.objects.filter(grupo=grupo)
    if vista == 'mensual':
        movimientos_qs = movimientos_qs.filter(
            fecha_hora__date__gte=mes_inicio, fecha_hora__date__lte=hoy
        )
        presupuesto_acum = (
            RegistroPresupuesto.objects
            .filter(grupo=grupo, tipo='Gasto', fecha__gte=mes_inicio, fecha__lte=hoy)
            .aggregate(t=Sum('monto'))['t'] or 0
        )
    else:
        presupuesto_acum = (
            RegistroPresupuesto.objects
            .filter(grupo=grupo, tipo='Gasto')
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
        .filter(grupo=grupo)
        .select_related('concepto', 'usuario')
        .order_by('-fecha_hora')[:5]
    )
    conceptos_gasto = Concepto.objects.filter(grupo=grupo, tipo='Gasto', activo=True)
    conceptos_ingreso = Concepto.objects.filter(grupo=grupo, tipo='Ingreso', activo=True)
    otros_miembros = (
        GrupoMiembro.objects.filter(grupo=grupo)
        .exclude(usuario=request.user)
        .select_related('usuario')
    )
    pendientes_count = GastoCompartido.objects.filter(
        usuario_deudor=request.user, grupo=grupo, pagado=False
    ).count()

    return render(request, 'finances/dashboard.html', {
        'grupo': grupo,
        'gasto_total': gasto_total,
        'ingreso_total': ingreso_total,
        'saldo_restante': saldo_restante,
        'desviacion': desviacion,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'ultimos_movimientos': ultimos,
        'conceptos_gasto': conceptos_gasto,
        'conceptos_ingreso': conceptos_ingreso,
        'otros_miembros': otros_miembros,
        'pendientes_count': pendientes_count,
        'hoy': hoy,
        'vista': vista,
    })


@login_required
def budget_view(request):
    grupo, redir = _require_group(request)
    if redir:
        return redir

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
                    fecha_fin = date.fromisoformat(fecha_fin_str + '-01')
                except ValueError:
                    pass
            try:
                concepto = Concepto.objects.get(id=concepto_id, grupo=grupo, activo=True)
                monto = int(monto_str)
                assert monto > 0
                registro = RegistroPresupuesto.objects.create(
                    tipo=tipo, concepto=concepto, nombre=nombre, detalle=detalle,
                    fecha=fecha_str, monto=monto, grupo=grupo, periodicidad=periodicidad,
                    fecha_fin=fecha_fin,
                )
                crear_notificaciones_grupo(
                    grupo, Notificacion.TIPO_PRESUPUESTO,
                    f'Se realizó un cambio en el presupuesto de {concepto.nombre}',
                    referencia_id=registro.id,
                    excluir_usuario=request.user,
                )
                messages.success(request, 'Registro de presupuesto agregado.')
            except Exception as e:
                messages.error(request, 'Error al agregar registro. Verifica los datos.')

        elif action == 'modify':
            registro_id = request.POST.get('registro_id')
            monto_str = request.POST.get('monto', '0').replace('.', '').replace(',', '')
            try:
                registro = RegistroPresupuesto.objects.get(id=registro_id, grupo=grupo)
                registro.monto = int(monto_str)
                registro.save()
                crear_notificaciones_grupo(
                    grupo, Notificacion.TIPO_PRESUPUESTO,
                    f'Se realizó un cambio en el presupuesto de {registro.concepto.nombre}',
                    referencia_id=registro.id,
                    excluir_usuario=request.user,
                )
                messages.success(request, 'Monto actualizado.')
            except Exception:
                messages.error(request, 'Error al modificar.')

        elif action == 'delete':
            registro_id = request.POST.get('registro_id')
            try:
                registro = RegistroPresupuesto.objects.get(id=registro_id, grupo=grupo)
                nombre = registro.concepto.nombre
                registro.delete()
                crear_notificaciones_grupo(
                    grupo, Notificacion.TIPO_PRESUPUESTO,
                    f'Se realizó un cambio en el presupuesto de {nombre}',
                    excluir_usuario=request.user,
                )
                messages.success(request, 'Registro eliminado.')
            except Exception:
                messages.error(request, 'Error al eliminar.')

        return redirect('finances-budget')

    hoy = date.today()
    MESES_ES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

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

    base_qs = RegistroPresupuesto.objects.filter(grupo=grupo).filter(
        Q(periodicidad='Mensual') |
        Q(periodicidad='Anual', fecha__month=mes) |
        Q(periodicidad='Puntual', fecha__year=anio, fecha__month=mes)
    ).filter(
        Q(fecha_fin__isnull=True) |
        Q(fecha_fin__year__gt=anio) |
        Q(fecha_fin__year=anio, fecha_fin__month__gte=mes)
    )

    registros = base_qs.select_related('concepto').order_by('-tipo', '-monto')
    ingresos = base_qs.filter(tipo='Ingreso').aggregate(t=Sum('monto'))['t'] or 0
    gastos   = base_qs.filter(tipo='Gasto').aggregate(t=Sum('monto'))['t'] or 0
    total = ingresos - gastos
    conceptos_gasto = Concepto.objects.filter(grupo=grupo, tipo='Gasto', activo=True)
    conceptos_ingreso = Concepto.objects.filter(grupo=grupo, tipo='Ingreso', activo=True)

    return render(request, 'finances/budget.html', {
        'grupo': grupo, 'registros': registros, 'total': total,
        'conceptos_gasto': conceptos_gasto, 'conceptos_ingreso': conceptos_ingreso,
        'mes_filtro': mes_filtro,
        'mes_nombre': MESES_ES[mes - 1],
        'mes_anio': anio,
        'prev_mes': prev_mes,
        'next_mes': next_mes,
    })


@login_required
def concepts_view(request):
    grupo, redir = _require_group(request)
    if redir:
        return redir

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            nombre = request.POST.get('nombre', '').strip()
            tipo = request.POST.get('tipo')
            if nombre and tipo in ('Gasto', 'Ingreso'):
                if Concepto.objects.filter(grupo=grupo, nombre__iexact=nombre, activo=True).exists():
                    messages.error(request, f'Ya existe un concepto llamado "{nombre}" en este grupo.')
                else:
                    Concepto.objects.create(nombre=nombre, tipo=tipo, grupo=grupo)
                    messages.success(request, 'Concepto agregado.')
            else:
                messages.error(request, 'Nombre y tipo son obligatorios.')

        elif action == 'edit':
            concepto_id = request.POST.get('concepto_id')
            nombre = request.POST.get('nombre', '').strip()
            try:
                c = Concepto.objects.get(id=concepto_id, grupo=grupo, activo=True)
                if Concepto.objects.filter(grupo=grupo, nombre__iexact=nombre, activo=True).exclude(id=concepto_id).exists():
                    messages.error(request, f'Ya existe un concepto llamado "{nombre}" en este grupo.')
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
                c = Concepto.objects.get(id=concepto_id, grupo=grupo, activo=True)
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
                            'grupo': grupo,
                            'conceptos': Concepto.objects.filter(grupo=grupo, activo=True),
                            'concepto_conflicto': c,
                        })
                    c.activo = False
                    c.save()
                    messages.success(request, 'Concepto eliminado.')
            except Concepto.DoesNotExist:
                messages.error(request, 'Concepto no encontrado.')

        return redirect('finances-concepts')

    conceptos = Concepto.objects.filter(grupo=grupo, activo=True).order_by('tipo', 'nombre')
    return render(request, 'finances/concepts.html', {'grupo': grupo, 'conceptos': conceptos})


@login_required
def movements_view(request):
    grupo, redir = _require_group(request)
    if redir:
        return redir

    qs = (
        Movimiento.objects
        .filter(grupo=grupo)
        .select_related('concepto', 'usuario')
        .order_by('-fecha_hora')
    )
    concepto_id = request.GET.get('concepto', '')
    if concepto_id:
        qs = qs.filter(concepto_id=concepto_id)

    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get('page', 1))
    conceptos = Concepto.objects.filter(grupo=grupo, activo=True).order_by('nombre')

    return render(request, 'finances/movements.html', {
        'grupo': grupo, 'page': page, 'conceptos': conceptos,
        'concepto_filtro': concepto_id,
    })


@login_required
def movement_detail_view(request, movement_id):
    grupo, redir = _require_group(request)
    if redir:
        return redir
    mov = get_object_or_404(Movimiento, id=movement_id, grupo=grupo)
    return render(request, 'finances/movement_detail.html', {'grupo': grupo, 'movimiento': mov})


@login_required
def export_csv_view(request):
    grupo, redir = _require_group(request)
    if redir:
        return redir

    movimientos = (
        Movimiento.objects.filter(grupo=grupo)
        .select_related('concepto', 'usuario')
        .order_by('-fecha_hora')
    )
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Tipo', 'Concepto', 'Nombre', 'Detalle', 'Monto', 'Usuario', 'Fecha y hora'])
    for m in movimientos:
        c_nombre = m.concepto.nombre if m.concepto and m.concepto.activo else 'Desconocido'
        writer.writerow([m.tipo, c_nombre, m.nombre, m.detalle, m.monto,
                         m.usuario.username, m.fecha_hora.strftime('%d/%m/%Y %H:%M')])
    content = '﻿' + output.getvalue()
    response = HttpResponse(content, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="movimientos.csv"'
    return response


@login_required
def add_movement_view(request):
    grupo, redir = _require_group(request)
    if redir:
        return redir

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        nombre = request.POST.get('nombre', '').strip()
        detalle = request.POST.get('detalle', '').strip()
        concepto_id = request.POST.get('concepto')
        monto_str = request.POST.get('monto', '0').replace('.', '').replace(',', '')
        es_compartido = request.POST.get('es_compartido') == '1'
        try:
            concepto = Concepto.objects.get(id=concepto_id, grupo=grupo, activo=True)
            monto = int(monto_str)
            assert monto > 0 and nombre
            mov = Movimiento.objects.create(
                tipo=tipo, nombre=nombre, detalle=detalle,
                monto=monto, concepto=concepto, usuario=request.user,
                grupo=grupo, fecha_hora=timezone.now(),
            )
            tipo_notif = Notificacion.TIPO_GASTO if tipo == 'Gasto' else Notificacion.TIPO_INGRESO
            titulo = f'Se {"generó un gasto" if tipo == "Gasto" else "registró un ingreso"} por ${monto:,} de {request.user.username} por {concepto.nombre}'.replace(',', '.')
            crear_notificaciones_grupo(grupo, tipo_notif, titulo, referencia_id=mov.id, excluir_usuario=request.user)

            if es_compartido and tipo == 'Gasto':
                usuario_deudor_id = request.POST.get('usuario_deudor', '')
                monto_comp_str = request.POST.get('monto_compartido', '0').replace('.', '').replace(',', '')
                try:
                    miembro = GrupoMiembro.objects.select_related('usuario').get(
                        usuario_id=usuario_deudor_id, grupo=grupo
                    )
                    monto_compartido = int(monto_comp_str)
                    assert monto_compartido > 0
                    GastoCompartido.objects.create(
                        movimiento=mov,
                        usuario_acreedor=request.user,
                        usuario_deudor=miembro.usuario,
                        monto_pendiente=monto_compartido,
                        grupo=grupo,
                    )
                    Notificacion.objects.create(
                        titulo=f'{request.user.username} te compartió un gasto de ${monto_compartido:,} por {concepto.nombre}. Pendiente de pago.'.replace(',', '.'),
                        tipo=Notificacion.TIPO_GASTO_COMPARTIDO,
                        referencia_id=mov.id,
                        usuario=miembro.usuario,
                    )
                except Exception:
                    pass

            messages.success(request, f'{tipo} registrado exitosamente.')
        except Exception:
            messages.error(request, 'Error al registrar. Verifica los datos.')

    return redirect('finances-dashboard')


@login_required
def gastos_compartidos_view(request):
    grupo, redir = _require_group(request)
    if redir:
        return redir

    if request.method == 'POST':
        gasto_id = request.POST.get('gasto_id')
        try:
            gasto = GastoCompartido.objects.get(
                id=gasto_id, usuario_acreedor=request.user, grupo=grupo, pagado=False
            )
            gasto.pagado = True
            gasto.save()
            Notificacion.objects.create(
                titulo=f'{request.user.username} marcó como pagado el gasto compartido de ${gasto.monto_pendiente:,} por {gasto.movimiento.concepto.nombre if gasto.movimiento.concepto else "sin concepto"}.'.replace(',', '.'),
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
        .filter(usuario_deudor=request.user, grupo=grupo, pagado=False)
        .select_related('movimiento__concepto', 'usuario_acreedor')
        .order_by('-created_at')
    )
    pendientes_cobro = (
        GastoCompartido.objects
        .filter(usuario_acreedor=request.user, grupo=grupo, pagado=False)
        .select_related('movimiento__concepto', 'usuario_deudor')
        .order_by('-created_at')
    )
    total_debo = pendientes_pago.aggregate(t=Sum('monto_pendiente'))['t'] or 0
    total_me_deben = pendientes_cobro.aggregate(t=Sum('monto_pendiente'))['t'] or 0

    return render(request, 'finances/shared_expenses.html', {
        'grupo': grupo,
        'pendientes_pago': pendientes_pago,
        'pendientes_cobro': pendientes_cobro,
        'total_debo': total_debo,
        'total_me_deben': total_me_deben,
    })
