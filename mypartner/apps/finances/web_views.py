import csv
import io
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from apps.groups.models import GrupoMiembro
from apps.notifications.models import Notificacion
from apps.notifications.services import crear_notificaciones_grupo
from .models import Concepto, Movimiento, RegistroPresupuesto


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

    movimientos_mes = Movimiento.objects.filter(
        grupo=grupo, fecha_hora__date__gte=mes_inicio, fecha_hora__date__lte=hoy
    )
    gasto_mensual = movimientos_mes.filter(tipo='Gasto').aggregate(t=Sum('monto'))['t'] or 0
    ingreso_mensual = movimientos_mes.filter(tipo='Ingreso').aggregate(t=Sum('monto'))['t'] or 0
    saldo_restante = ingreso_mensual - gasto_mensual

    presupuesto_acum = (
        RegistroPresupuesto.objects
        .filter(grupo=grupo, tipo='Gasto', fecha__lte=hoy)
        .aggregate(t=Sum('monto'))['t'] or 0
    )
    desviacion = presupuesto_acum - gasto_mensual

    gastos_concepto = (
        movimientos_mes.filter(tipo='Gasto')
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

    return render(request, 'finances/dashboard.html', {
        'grupo': grupo,
        'gasto_mensual': gasto_mensual,
        'saldo_restante': saldo_restante,
        'desviacion': desviacion,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'ultimos_movimientos': ultimos,
        'conceptos_gasto': conceptos_gasto,
        'conceptos_ingreso': conceptos_ingreso,
        'hoy': hoy,
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
            try:
                concepto = Concepto.objects.get(id=concepto_id, grupo=grupo, activo=True)
                monto = int(monto_str)
                assert monto > 0
                registro = RegistroPresupuesto.objects.create(
                    tipo=tipo, concepto=concepto, nombre=nombre, detalle=detalle,
                    fecha=fecha_str, monto=monto, grupo=grupo
                )
                crear_notificaciones_grupo(
                    grupo, Notificacion.TIPO_PRESUPUESTO,
                    f'Se realizó un cambio en el presupuesto de {concepto.nombre}',
                    referencia_id=registro.id,
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
                )
                messages.success(request, 'Registro eliminado.')
            except Exception:
                messages.error(request, 'Error al eliminar.')

        return redirect('finances-budget')

    registros = (
        RegistroPresupuesto.objects
        .filter(grupo=grupo)
        .select_related('concepto')
        .order_by('tipo', 'concepto__nombre')
    )
    total = registros.aggregate(t=Sum('monto'))['t'] or 0
    conceptos_gasto = Concepto.objects.filter(grupo=grupo, tipo='Gasto', activo=True)
    conceptos_ingreso = Concepto.objects.filter(grupo=grupo, tipo='Ingreso', activo=True)

    return render(request, 'finances/budget.html', {
        'grupo': grupo, 'registros': registros, 'total': total,
        'conceptos_gasto': conceptos_gasto, 'conceptos_ingreso': conceptos_ingreso,
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
                Concepto.objects.create(nombre=nombre, tipo=tipo, grupo=grupo)
                messages.success(request, 'Concepto agregado.')
            else:
                messages.error(request, 'Nombre y tipo son obligatorios.')

        elif action == 'edit':
            concepto_id = request.POST.get('concepto_id')
            nombre = request.POST.get('nombre', '').strip()
            try:
                c = Concepto.objects.get(id=concepto_id, grupo=grupo, activo=True)
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
            accion = 'gasto' if tipo == 'Gasto' else 'ingreso'
            titulo = f'Se {"generó un gasto" if tipo == "Gasto" else "registró un ingreso"} por ${monto:,} de {request.user.username} por {concepto.nombre}'.replace(',', '.')
            crear_notificaciones_grupo(grupo, tipo_notif, titulo, referencia_id=mov.id)
            messages.success(request, f'{tipo} registrado exitosamente.')
        except Exception:
            messages.error(request, 'Error al registrar. Verifica los datos.')

    return redirect('finances-dashboard')
