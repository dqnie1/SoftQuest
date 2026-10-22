import json
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.decorators.http import require_POST

from contenido.models import Mundo, Insignia, InsigniaUsuario
from minijuegos.examen.models import IntentoExamen
from minijuegos.examen.operaciones.OperacionesExamen import OperacionesExamen, ExcepcionCargaExamen


@login_required
def examen_inicio(request, mundo_id):
    """
    Pantalla previa con las instrucciones del examen final del mundo (Flujo 1.0 - Pasos 1 y 2).
    Maneja también la Excepción 1.0.E1 si el examen no se puede cargar.
    """
    ops = OperacionesExamen()
    usuario = ops.obtener_usuario(request)
    mundo = get_object_or_404(Mundo, id=mundo_id)

    # RN-39: Verificar si completó todas las actividades del mundo
    habilitado = ops.verificar_habilitado(usuario, mundo)
    if not habilitado:
        return render(request, 'examen_bloqueado.html', {
            'mundo': mundo,
            'usuario': usuario,
            'url_temario': reverse('temario_mundo', kwargs={'mundo_id': mundo.id})
        })

    # Verificar disponibilidad del banco de reactivos (1.0.E1)
    try:
        examen_preview = ops.generar_examen(mundo)
    except ExcepcionCargaExamen as e:
        return render(request, 'examen_error.html', {
            'mundo': mundo,
            'mensaje_error': str(e),
            'url_temario': reverse('temario_mundo', kwargs={'mundo_id': mundo.id})
        })

    # Formatear tiempo límite a minutos
    minutos_limite = ops.TIEMPO_GLOBAL_SEGUNDOS // 60

    context = {
        'mundo': mundo,
        'usuario': usuario,
        'total_bloques': examen_preview['total_bloques'],
        'tiempo_minutos': minutos_limite,
        'minimo_aprobatorio': int(ops.CALIFICACION_MINIMA),
        'url_temario': reverse('temario_mundo', kwargs={'mundo_id': mundo.id}),
        'url_comenzar': reverse('examen:examen_presentar', kwargs={'mundo_id': mundo.id})
    }
    return render(request, 'examen_inicio.html', context)


@login_required
def examen_presentar(request, mundo_id):
    """
    Pantalla interactiva de presentación del examen con cronómetro global,
    bloques secuenciales (RN-40, RN-43) y modales de aviso/confirmación.
    """
    ops = OperacionesExamen()
    usuario = ops.obtener_usuario(request)
    mundo = get_object_or_404(Mundo, id=mundo_id)

    # RN-39: Verificar habilitación
    if not ops.verificar_habilitado(usuario, mundo):
        return redirect('examen:examen_inicio', mundo_id=mundo.id)

    # Generar reactivos aleatorios para este intento (RN-41)
    try:
        examen_data = ops.generar_examen(mundo)
    except ExcepcionCargaExamen as e:
        return render(request, 'examen_error.html', {
            'mundo': mundo,
            'mensaje_error': str(e),
            'url_temario': reverse('temario_mundo', kwargs={'mundo_id': mundo.id})
        })

    # Guardar claves y datos sensibles en la sesión del usuario (RN-42)
    session_key = f"examen_activo_{mundo.id}"
    request.session[session_key] = {
        'claves': examen_data['claves'],
        'bloques': examen_data['bloques'],
        'total_reactivos': examen_data['total_reactivos'],
        'inicio_timestamp': time.time(),
        'mundo_id': mundo.id
    }
    request.session.modified = True

    context = {
        'mundo': mundo,
        'usuario': usuario,
        'bloques_json': json.dumps(examen_data['bloques']),
        'total_bloques': examen_data['total_bloques'],
        'tiempo_limite_segundos': ops.TIEMPO_GLOBAL_SEGUNDOS,
        'url_calificar': reverse('examen:examen_calificar', kwargs={'mundo_id': mundo.id}),
        'url_abandonar': reverse('temario_mundo', kwargs={'mundo_id': mundo.id}),
    }
    return render(request, 'examen_presentar.html', context)


@login_required
@require_POST
def examen_calificar(request, mundo_id):
    """
    Recibe las respuestas enviadas por el jugador, evalúa las claves almacenadas
    en la sesión y registra el intento (RN-44, RN-45, RN-51).
    """
    ops = OperacionesExamen()
    usuario = ops.obtener_usuario(request)
    mundo = get_object_or_404(Mundo, id=mundo_id)

    session_key = f"examen_activo_{mundo.id}"
    examen_session = request.session.get(session_key)

    if not examen_session:
        return JsonResponse({'error': 'No hay un examen activo en sesión.'}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos de respuesta inválidos.'}, status=400)

    respuestas_usuario = data.get('respuestas', {})
    tiempo_cliente = data.get('tiempo_empleado', 0)

    # Calcular tiempo real con base en el timestamp de inicio
    inicio_ts = examen_session.get('inicio_timestamp', time.time())
    tiempo_real = int(time.time() - inicio_ts)
    tiempo_empleado = max(tiempo_cliente, tiempo_real)

    # Evaluar y registrar intento
    resultado = ops.evaluar_y_registrar(
        usuario=usuario,
        mundo=mundo,
        examen_session_data=examen_session,
        respuestas_usuario=respuestas_usuario,
        tiempo_empleado=tiempo_empleado
    )

    # Limpiar examen de la sesión
    if session_key in request.session:
        del request.session[session_key]
        request.session.modified = True

    url_resultado = reverse('examen:examen_resultado', kwargs={'intento_id': resultado['intento'].id})
    return JsonResponse({'success': True, 'redirect_url': url_resultado})


@login_required
def examen_resultado(request, intento_id):
    """
    Pantalla de resultados (Flujo 1.0 - Pasos 13 a 16 / Flujo Alternativo 1.1).
    Muestra calificación, tiempo empleado, desglose por bloque y retroalimentación
    pedagógica de los reactivos incorrectos.
    """
    ops = OperacionesExamen()
    usuario = ops.obtener_usuario(request)
    intento = get_object_or_404(IntentoExamen, id=intento_id, usuario=usuario)

    minutos = intento.tiempo_empleado_segundos // 60
    segundos = intento.tiempo_empleado_segundos % 60
    tiempo_formateado = f"{minutos}m {segundos:02d}s"

    context = {
        'intento': intento,
        'mundo': intento.mundo,
        'usuario': usuario,
        'tiempo_formateado': tiempo_formateado,
        'resultado_bloques': intento.resultado_bloques.values(),
        'detalles_reactivos': intento.detalles_reactivos,
        'total_errores': len(intento.detalles_reactivos),
        'url_reintentar': reverse('examen:examen_inicio', kwargs={'mundo_id': intento.mundo.id}),
        'url_temario': reverse('temario_mundo', kwargs={'mundo_id': intento.mundo.id}),
        'url_mapa': reverse('mapa_mundos')
    }
    return render(request, 'examen_resultado.html', context)
