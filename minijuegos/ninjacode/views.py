import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from contenido.models import Actividad, ProgresoActividad
from contenido.operaciones.OperacionesContenido import OperacionesContenido
from .models import NinjaCode
from .operaciones.OperacionesNinjaCode import OperacionesNinjaCode


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


@login_required
def jugar(request, actividad_id):
    actividad = get_object_or_404(
        Actividad.objects.select_related('temario'),
        pk=actividad_id,
        tipo='ninjacode',
    )
    temario_url = _url_temario(actividad)
    ninjacode = NinjaCode.objects.filter(pk=actividad_id).prefetch_related('requisitos').first()
    ops = OperacionesNinjaCode()
    requisitos = ops.cargar_requisitos(ninjacode)
    if ninjacode is None or not ops.tiene_contenido(requisitos):
        return render(request, 'ninjacode/error.html', {'temario_url': temario_url})

    return render(request, 'ninjacode/jugar.html', {
        'temario_url': temario_url,
        'guardar_url': reverse('ninjacode:guardar_progreso', args=[actividad.id]),
        'frutas': ops.serializar_requisitos(requisitos),
        'config': {
            'idActividad': actividad.id,
            'puntosAcierto': ops.PUNTOS_ACIERTO,
            'vidas': ops.VIDAS,
            'frutasNivel': ops.FRUTAS_POR_NIVEL,
            'aciertosMazo': ops.ACIERTOS_EN_MAZO,
            'puntosMax': actividad.puntos_max or 100,
        },
    })


@require_POST
@login_required
def guardar_progreso(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id, tipo='ninjacode')
    usuario = OperacionesContenido().obtener_usuario(request)
    if usuario is None:
        return JsonResponse({'guardado': False, 'error': 'Usuario no identificado'}, status=401)

    try:
        datos = json.loads(request.body or b'{}')
        cortes = datos['cortes']
        niveles_completados = int(datos['niveles_completados'])
        if not isinstance(cortes, list):
            raise TypeError
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'guardado': False, 'error': 'Datos invalidos'}, status=400)

    ninjacode = NinjaCode.objects.filter(pk=actividad_id).prefetch_related('requisitos').first()
    ops = OperacionesNinjaCode()
    requisitos = ops.cargar_requisitos(ninjacode)
    if ninjacode is None or not ops.tiene_contenido(requisitos):
        return JsonResponse({'guardado': False, 'error': 'No fue posible cargar las frutas'}, status=400)

    resultado = ops.evaluar_partida(
        requisitos,
        cortes,
        niveles_completados,
        actividad.puntos_max or 100,
    )
    if not resultado.get('ok'):
        return JsonResponse({'guardado': False, 'error': resultado.get('error', 'Datos invalidos')}, status=400)

    if not resultado['completado']:
        return JsonResponse({
            'guardado': False,
            'completado': False,
            'error': 'La actividad no se completo',
        })

    previo = ProgresoActividad.objects.filter(usuario=usuario, actividad=actividad).first()
    ProgresoActividad.objects.update_or_create(
        usuario=usuario,
        actividad=actividad,
        defaults={
            'estado': 'completado',
            'puntaje': resultado['puntaje'],
            'intentos': (previo.intentos or 0) + 1 if previo else 1,
            'fecha_completado': timezone.now(),
        },
    )
    OperacionesContenido().actualizar_progreso_mundo(usuario)
    return JsonResponse({
        'guardado': True,
        'completado': True,
        'puntaje': resultado['puntaje'],
        'aciertos': resultado['aciertos'],
        'errores': resultado['errores'],
        'score1': resultado['score1'],
        'score2': resultado['score2'],
    })
