import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from contenido.models import Actividad
from .models import CodeBreaker
from .operaciones.OperacionesCodeBreaker import OperacionesCodeBreaker as Ops


def _url_temario(actividad):
    """Devuelve la URL del temario al que pertenece la actividad o el mapa de mundos."""
    try:
        if actividad and actividad.temario and actividad.temario.mundo_id:
            return reverse("temario_mundo", args=[actividad.temario.mundo_id])
    except Exception:
        pass
    try:
        return reverse("mapa_mundos")
    except Exception:
        return "/"


def _datos_json(request):
    try:
        return json.loads(request.body.decode('utf-8') or "{}")
    except (ValueError, UnicodeDecodeError):
        return {}


@login_required
@require_GET
def vista_codebreaker(request, actividad_id):
    """
    CU-11 Flujo Normal:
    Paso 1: El sistema recupera la actividad con sus ocho conceptos.
    Paso 2: Muestra instrucciones de la actividad y la opción "Comenzar".
    Excepción 1.0.E1: Si no puede recuperar los datos, muestra alerta y regresa al temario.
    """
    actividad = get_object_or_404(Actividad, pk=actividad_id)
    url_regreso = _url_temario(actividad)

    cb = Ops.obtener_codebreaker(actividad_id)

    # Excepción 1.0.E1: Error en la carga de la actividad
    if cb is None or cb.conceptos.count() == 0:
        messages.error(
            request,
            "No fue posible cargar la actividad CodeBreaker. Por favor intenta más tarde."
        )
        return redirect(url_regreso)

    conceptos = Ops.obtener_conceptos(cb)

    context = {
        "actividad": actividad,
        "codebreaker": cb,
        "conceptos_json": json.dumps(conceptos),
        "url_temario": url_regreso,
        "url_finalizar": reverse("codebreaker:finalizar", kwargs={"actividad_id": actividad.pk}),
    }

    return render(request, "codebreaker/codebreaker.html", context)


@login_required
@require_POST
def finalizar_partida(request, actividad_id):
    """
    Endpoint para registrar el resultado de la partida.
    RN-108, RN-111, RN-113: Registra conceptos recolectados, vidas perdidas, XP y actualiza progreso.
    """
    actividad = get_object_or_404(Actividad, pk=actividad_id)
    datos = _datos_json(request)

    vidas_perdidas = datos.get("vidas_perdidas", 0)
    conceptos_ids = datos.get("conceptos_ids", [])
    completada = bool(datos.get("completada", False))

    resultado = Ops.registrar_resultado(
        actividad=actividad,
        usuario_cuenta=request.user,
        vidas_perdidas=vidas_perdidas,
        conceptos_ids=conceptos_ids,
        completada=completada,
    )

    return JsonResponse(resultado)


@login_required
@require_GET
def datos_partida(request, actividad_id):
    """
    Endpoint de apoyo para obtener los conceptos y configuración del juego en formato JSON.
    """
    cb = Ops.obtener_codebreaker(actividad_id)
    if not cb:
        return JsonResponse({"ok": False, "error": "Actividad no encontrada"}, status=404)

    return JsonResponse({
        "ok": True,
        "filas": cb.filas,
        "columnas": cb.columnas,
        "bloques_totales": cb.bloques_totales,
        "bloques_especiales": cb.bloques_especiales,
        "conceptos": Ops.obtener_conceptos(cb),
    })
