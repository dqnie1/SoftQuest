import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from contenido.models import Actividad
from .models import SopaLetras
from .operaciones.OperacionesSopaLetras import OperacionesSopaLetras as Ops


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
def vista_sopaletras(request, actividad_id):
    """
    CU-12 Flujo Normal:
    Paso 1: El sistema recupera la sopa de letras con su cuadrícula, palabras y definiciones.
    Paso 2: Muestra instrucciones de la actividad y la opción "Comenzar".
    Excepción 1.0.E1: Si no puede recuperar los datos, muestra alerta y regresa al temario.
    """
    actividad = get_object_or_404(Actividad, pk=actividad_id)
    url_regreso = _url_temario(actividad)

    sopa = Ops.obtener_sopa_letras(actividad_id)

    # Excepción 1.0.E1: Error en la carga de la sopa de letras
    if sopa is None or sopa.palabras.count() == 0:
        messages.error(
            request,
            "No fue posible cargar la actividad Sopa de Letras. Por favor intenta más tarde."
        )
        return redirect(url_regreso)

    palabras = Ops.obtener_palabras(sopa)

    context = {
        "actividad": actividad,
        "sopaletras": sopa,
        "palabras_json": json.dumps(palabras),
        "url_temario": url_regreso,
        "url_finalizar": reverse("sopaletras:finalizar", kwargs={"actividad_id": actividad.pk}),
    }

    return render(request, "sopaletras/sopaletras.html", context)


@login_required
@require_POST
def finalizar_partida(request, actividad_id):
    """
    POST-2, POST-4, RN-92, RN-93: Endpoint para registrar el resultado final de la sopa de letras.
    """
    actividad = get_object_or_404(Actividad, pk=actividad_id)
    datos = _datos_json(request)

    errores = datos.get("errores", 0)
    pista_usada = bool(datos.get("pista_usada", False))
    tiempo_segundos = datos.get("tiempo_segundos", 0)
    completada = bool(datos.get("completada", True))

    resultado = Ops.registrar_resultado(
        actividad=actividad,
        usuario_cuenta=request.user,
        errores=errores,
        pista_usada=pista_usada,
        tiempo_segundos=tiempo_segundos,
        completada=completada,
    )

    return JsonResponse(resultado)


@login_required
@require_GET
def datos_partida(request, actividad_id):
    """
    Endpoint de soporte para obtener las palabras y configuración en formato JSON.
    """
    sopa = Ops.obtener_sopa_letras(actividad_id)
    if not sopa:
        return JsonResponse({"ok": False, "error": "Actividad no encontrada"}, status=404)

    return JsonResponse({
        "ok": True,
        "dimension": sopa.dimension,
        "total_palabras": sopa.total_palabras,
        "palabras": Ops.obtener_palabras(sopa),
    })
