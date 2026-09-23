import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from contenido.models import Actividad, ProgresoActividad
from .models import Concepto
from .operaciones.OperacionesMatch import OperacionesMatch


def obtenerConceptos(request, id_match=None):
    conceptos = OperacionesMatch().obtenerTerminosYDefinicionesRevuelta(id_match)

    return render(request, 'match.html', {
        'conceptos': conceptos,
        'hay_conceptos': bool(conceptos),
        'id_match': id_match,
    })


@require_POST
def validar_match(request):
    try:
        datos = json.loads(request.body)
        id_match = int(datos['id_match'])
        parejas = datos['parejas']
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Datos invalidos'}, status=400)

    correctas = {
        c['termino_id']: c['definicion_id']
        for c in OperacionesMatch().obtenerListaConceptosCorrecta(id_match)
    }

    detalles = []
    aciertos = 0

    for pareja in parejas:
        try:
            termino_id = int(pareja['termino_id'])
            definicion_id = int(pareja['definicion_id'])
        except (TypeError, ValueError, KeyError):
            return JsonResponse({'error': 'Pareja invalida'}, status=400)

        correcta = correctas.get(termino_id) == definicion_id
        if correcta:
            aciertos += 1

        detalles.append({
            'termino_id': termino_id,
            'definicion_id': definicion_id,
            'correcta': correcta,
        })

    total = len(parejas)
    porcentaje = round((aciertos / total) * 100) if total else 0

    return JsonResponse({
        'aciertos': aciertos,
        'total': total,
        'porcentaje': porcentaje,
        'completado': aciertos == total,
        'detalles': detalles,
    })


@require_POST
def guardar_progreso(request):
    try:
        datos = json.loads(request.body)

        id_actividad = int(datos['id_actividad'])
        intentos = int(datos.get('intentos', 0))

    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({
            'guardado': False,
            'error': 'Datos invalidos'
        }, status=400)

    if request.user.is_authenticated:
        try:
            actividad = Actividad.objects.get(pk=id_actividad)

            ProgresoActividad.objects.update_or_create(
                usuario_id=request.user.id,
                actividad=actividad,
                defaults={
                    'estado': 'completado',
                    'intentos': intentos
                },
            )

        except Actividad.DoesNotExist:
            return JsonResponse({
                'guardado': False,
                'error': 'Actividad no encontrada'
            }, status=404)

    return JsonResponse({
        'guardado': True
    })
