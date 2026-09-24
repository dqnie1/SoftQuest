import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from contenido.models import Actividad, ProgresoActividad
from contenido.operaciones.OperacionesContenido import OperacionesContenido
from .models import Pregunta, Respuesta, Trivia
from .operaciones.OperacionesTrivia import OperacionesTrivia


def obtener_preguntas(request, id_trivia=None):
    ops = OperacionesTrivia()
    preguntas = Pregunta.todas_las_preguntas(id_trivia) or []

    titulo = 'Trivia'
    if id_trivia is not None:
        try:
            trivia = Trivia.objects.select_related('actividad').get(pk=id_trivia)
            titulo = trivia.actividad.titulo
        except Trivia.DoesNotExist:
            titulo = 'Trivia'

    preguntas_payload = []
    for pregunta in preguntas:
        respuestas = ops.revolver_respuestas(list(pregunta.respuestas.all()))
        preguntas_payload.append({
            'id': pregunta.id,
            'texto': pregunta.texto,
            'respuestas': [
                {'id': r.id, 'texto': r.texto}
                for r in respuestas
            ],
        })

    return render(request, 'Trivia.html', {
        'preguntas': preguntas_payload,
        'hay_preguntas': bool(preguntas_payload),
        'id_trivia': id_trivia,
        'total_preguntas': len(preguntas_payload),
        'umbral': OperacionesTrivia.UMBRAL_APROBATORIO,
        'titulo_actividad': titulo,
    })


@require_POST
def validar_respuesta(request):
    try:
        datos = json.loads(request.body)
        id_pregunta = int(datos['pregunta_id'])
        id_respuesta = int(datos['respuesta_id'])
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'error': 'Datos invalidos'}, status=400)

    try:
        respuesta = Respuesta.objects.select_related('pregunta').get(
            pk=id_respuesta,
            pregunta_id=id_pregunta,
        )
    except Respuesta.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Respuesta no encontrada'}, status=404)

    ops = OperacionesTrivia()
    correcto = ops.validar_respuesta(respuesta)
    correcta = Respuesta.objects.filter(
        pregunta_id=id_pregunta,
        es_correcta=True,
    ).first()

    return JsonResponse({
        'ok': True,
        'correcto': correcto,
        'pregunta_id': id_pregunta,
        'respuesta_id': id_respuesta,
        'respuesta_correcta_id': correcta.id if correcta else None,
        'respuesta_correcta_texto': correcta.texto if correcta else '',
    })


@require_POST
def guardar_progreso(request):
    try:
        datos = json.loads(request.body)
        id_actividad = int(datos['id_actividad'])
        intentos = int(datos.get('intentos', 0))
        puntaje = max(0, min(100, int(datos.get('puntaje', 0))))
        aprobado = bool(datos.get('aprobado', False))
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'guardado': False, 'error': 'Datos invalidos'}, status=400)

    usuario = OperacionesContenido().obtener_usuario(request)

    if usuario is None:
        return JsonResponse(
            {'guardado': False, 'error': 'Usuario no identificado'},
            status=401,
        )

    try:
        actividad = Actividad.objects.get(pk=id_actividad)
        estado = 'completado' if aprobado else 'reprobado'
        ProgresoActividad.objects.update_or_create(
            usuario=usuario,
            actividad=actividad,
            defaults={
                'estado': estado,
                'intentos': intentos,
                'puntaje': puntaje,
            },
        )
        if aprobado:
            OperacionesContenido().actualizar_progreso_mundo(usuario)
    except Actividad.DoesNotExist:
        return JsonResponse(
            {'guardado': False, 'error': 'Actividad no encontrada'},
            status=404,
        )

    return JsonResponse({'guardado': True})
