import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from contenido.models import Actividad, ProgresoActividad
from contenido.operaciones.OperacionesContenido import OperacionesContenido
from .models import CubeCode, EjercicioCubeCode, ProgresoCubeCode
from .operaciones.OperacionesCubeCode import OperacionesCubeCode


def _url_temario(actividad):
    try:
        if actividad and actividad.temario_id and actividad.temario.mundo_id:
            return reverse('temario_mundo', args=[actividad.temario.mundo_id])
    except Exception:
        pass
    try:
        return reverse('mapa_mundos')
    except Exception:
        return '/'


def _total_ejercicios(cubecode):
    return EjercicioCubeCode.objects.filter(nivel__cubecode=cubecode).count()


def _obtener_progreso(usuario, cubecode):
    progreso, _ = ProgresoCubeCode.objects.get_or_create(
        usuario=usuario,
        cubecode=cubecode,
    )
    return progreso


def _guardar_actividad(usuario, actividad, progreso, completo):
    estado = 'completado' if completo else 'en_progreso'
    obj, created = ProgresoActividad.objects.get_or_create(
        usuario=usuario,
        actividad=actividad,
        defaults={
            'estado': estado,
            'puntaje': progreso.puntaje,
            'intentos': progreso.intentos,
            'fecha_inicio': timezone.now(),
            'fecha_completado': timezone.now() if completo else None,
        },
    )
    if created:
        return obj
    obj.puntaje = progreso.puntaje
    obj.intentos = progreso.intentos
    if completo:
        obj.estado = 'completado'
        if not obj.fecha_completado:
            obj.fecha_completado = timezone.now()
    elif obj.estado != 'completado':
        obj.estado = 'en_progreso'
    if not obj.fecha_inicio:
        obj.fecha_inicio = timezone.now()
    obj.save()
    return obj


@login_required
def jugar(request, actividad_id):
    actividad = get_object_or_404(
        Actividad.objects.select_related('temario'),
        pk=actividad_id,
        tipo='cubecode',
    )
    cubecode = (
        CubeCode.objects.filter(pk=actividad_id)
        .prefetch_related('niveles__ejercicios__bloques')
        .first()
    )
    temario_url = _url_temario(actividad)
    if cubecode is None or not cubecode.niveles.exists():
        return render(request, 'cubecode/error.html', {'temario_url': temario_url})

    usuario = OperacionesContenido().obtener_usuario(request)
    progreso = _obtener_progreso(usuario, cubecode)
    hechos = [int(item) for item in (progreso.ejercicios_hechos or [])]
    ops = OperacionesCubeCode()
    actual = ops.ejercicio_actual(cubecode, hechos)
    total = _total_ejercicios(cubecode)
    context = {
        'temario_url': temario_url,
        'salir_url': reverse('cubecode:salir', args=[actividad.id]),
        'comprobar_url': reverse('cubecode:comprobar', args=[actividad.id]),
        'terminado': actual is None and total > 0,
        'score': progreso.puntaje,
        'ejercicios_hechos': len(hechos),
        'ejercicios_total': total,
        'ejercicio': ops.serializar_ejercicio(actual, hechos, progreso.puntaje) if actual else None,
    }
    return render(request, 'cubecode/jugar.html', context)


@login_required
@require_POST
def comprobar(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id, tipo='cubecode')
    cubecode = get_object_or_404(CubeCode, pk=actividad_id)
    usuario = OperacionesContenido().obtener_usuario(request)
    if usuario is None:
        return JsonResponse({'ok': False, 'error': 'Usuario no identificado'}, status=401)

    try:
        datos = json.loads(request.body or b'{}')
        ejercicio_id = int(datos['ejercicio_id'])
        bloques = datos['bloques']
        if not isinstance(bloques, list):
            raise TypeError
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'error': 'Datos invalidos'}, status=400)

    ejercicio = (
        EjercicioCubeCode.objects.select_related('nivel')
        .filter(pk=ejercicio_id, nivel__cubecode=cubecode)
        .first()
    )
    if ejercicio is None:
        return JsonResponse({'ok': False, 'error': 'Ejercicio no encontrado'}, status=404)

    ops = OperacionesCubeCode()
    correcto = ops.validar_solucion(ejercicio, bloques)
    total = _total_ejercicios(cubecode)

    with transaction.atomic():
        progreso, _ = ProgresoCubeCode.objects.get_or_create(
            usuario=usuario,
            cubecode=cubecode,
        )
        progreso = ProgresoCubeCode.objects.select_for_update().get(pk=progreso.pk)
        hechos = [int(item) for item in (progreso.ejercicios_hechos or [])]
        if correcto and ejercicio.id not in hechos:
            hechos.append(ejercicio.id)
        progreso.ejercicios_hechos = hechos
        progreso.puntaje = ops.calcular_puntaje(len(hechos), total)
        progreso.intentos = (progreso.intentos or 0) + 1
        progreso.save()
        completo = total > 0 and len(hechos) >= total
        _guardar_actividad(usuario, actividad, progreso, completo)

    if completo:
        OperacionesContenido().actualizar_progreso_mundo(usuario)

    if not correcto:
        return JsonResponse({'ok': True, 'correcto': False, 'score': progreso.puntaje})

    siguiente = ops.ejercicio_actual(cubecode, hechos)
    respuesta = {
        'ok': True,
        'correcto': True,
        'score': progreso.puntaje,
        'completados_nivel': ejercicio.nivel.ejercicios.filter(id__in=hechos).count(),
        'total_nivel': ejercicio.nivel.ejercicios.count(),
    }
    if siguiente is None:
        respuesta['accion'] = 'fin'
        respuesta['resumen_final'] = {
            'score': progreso.puntaje,
            'ejercicios': len(hechos),
            'total': total,
        }
    elif siguiente.nivel_id != ejercicio.nivel_id:
        respuesta['accion'] = 'nivel'
        respuesta['resumen_nivel'] = {
            'numero': ejercicio.nivel.numero,
            'nombre': ejercicio.nivel.nombre,
            'ejercicios': ejercicio.nivel.ejercicios.count(),
            'score_nivel': ops.puntaje_del_nivel(cubecode, ejercicio.nivel, total),
            'score_total': progreso.puntaje,
        }
        respuesta['ejercicio'] = ops.serializar_ejercicio(siguiente, hechos, progreso.puntaje)
    else:
        respuesta['accion'] = 'siguiente'
        respuesta['ejercicio'] = ops.serializar_ejercicio(siguiente, hechos, progreso.puntaje)
    return JsonResponse(respuesta)


@login_required
@require_POST
def salir(request, actividad_id):
    actividad = get_object_or_404(
        Actividad.objects.select_related('temario'),
        pk=actividad_id,
        tipo='cubecode',
    )
    cubecode = CubeCode.objects.filter(pk=actividad_id).first()
    usuario = OperacionesContenido().obtener_usuario(request)
    if usuario is None or cubecode is None:
        return redirect(_url_temario(actividad))

    progreso = _obtener_progreso(usuario, cubecode)
    total = _total_ejercicios(cubecode)
    completo = total > 0 and len(progreso.ejercicios_hechos or []) >= total
    if completo:
        return redirect(_url_temario(actividad))
    _guardar_actividad(usuario, actividad, progreso, False)
    return redirect('cubecode:salida', actividad_id=actividad.id)


@login_required
def salida(request, actividad_id):
    actividad = get_object_or_404(
        Actividad.objects.select_related('temario'),
        pk=actividad_id,
        tipo='cubecode',
    )
    cubecode = CubeCode.objects.filter(pk=actividad_id).prefetch_related('niveles__ejercicios').first()
    temario_url = _url_temario(actividad)
    if cubecode is None:
        return render(request, 'cubecode/error.html', {'temario_url': temario_url})

    usuario = OperacionesContenido().obtener_usuario(request)
    progreso = _obtener_progreso(usuario, cubecode)
    hechos = [int(item) for item in (progreso.ejercicios_hechos or [])]
    ops = OperacionesCubeCode()
    actual = ops.ejercicio_actual(cubecode, hechos)
    if actual is None:
        return redirect(temario_url)

    hechos_nivel = actual.nivel.ejercicios.filter(id__in=hechos).count()
    return render(request, 'cubecode/salida.html', {
        'temario_url': temario_url,
        'jugar_url': reverse('cubecode:jugar', args=[actividad.id]),
        'nivel_numero': actual.nivel.numero,
        'nivel_nombre': actual.nivel.nombre,
        'hechos_nivel': hechos_nivel,
        'total_nivel': actual.nivel.ejercicios.count(),
    })
