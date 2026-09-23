import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from contenido.models import Actividad, ProgresoActividad, Usuario
from .models import Par
from .operaciones.OperacionesMemorama import OperacionesMemorama


def obetenerPares(request, id_memorama=None):
    pares = Par.todos_los_pares(id_memorama) or []
    pares = OperacionesMemorama().revolverPares(pares)

    return render(request, 'Memorama.html', {
        'pares': pares,
        'hay_pares': bool(pares),
        'id_memorama': id_memorama,
    })


@require_POST
def validar_par(request):
    try:
        datos = json.loads(request.body)
        primera = int(datos['primera_carta_id'])
        segunda = int(datos['segunda_carta_id'])
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'correcto': False, 'error': 'Datos invalidos'}, status=400)

    correcto = OperacionesMemorama().validarPar(primera, segunda)
    return JsonResponse({'correcto': correcto})


@require_POST
def guardar_progreso(request):
    try:
        datos = json.loads(request.body)
        id_actividad = int(datos['id_actividad'])
        intentos = int(datos.get('intentos', 0))
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'guardado': False, 'error': 'Datos invalidos'}, status=400)

    usuario = None
    if request.user.is_authenticated:
        usuario = Usuario.objects.filter(email=request.user.email).first()
        if usuario is None:
            usuario = Usuario.objects.filter(pk=request.user.id).first()

    if usuario is None:
        return JsonResponse(
            {'guardado': False, 'error': 'Usuario no identificado'},
            status=401,
        )

    try:
        actividad = Actividad.objects.get(pk=id_actividad)
        ProgresoActividad.objects.update_or_create(
            usuario=usuario,
            actividad=actividad,
            defaults={
                'estado': 'completado',
                'intentos': intentos,
            },
        )
    except Actividad.DoesNotExist:
        return JsonResponse({'guardado': False, 'error': 'Actividad no encontrada'}, status=404)

    return JsonResponse({'guardado': True})