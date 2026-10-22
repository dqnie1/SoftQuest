import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from contenido.models import Actividad, ProgresoActividad
from .models import Snake, NivelSnake
from .operaciones.OperacionesSnake import OperacionesSnake as Ops


# ----------------------------------------------------------------------
# Utilidades de navegacion y progreso
# ----------------------------------------------------------------------
def _url_temario(actividad):
    """Devuelve la URL del temario al que pertenece la actividad o el mapa general."""
    try:
        if actividad and actividad.temario and actividad.temario.mundo_id:
            return reverse("temario_mundo", args=[actividad.temario.mundo_id])
    except Exception:
        pass
    try:
        return reverse("mapa_mundos")
    except Exception:
        return "/"


def _datos(request):
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        return {}


def _guardar_progreso(actividad, usuario_cuenta, puntaje, completada):
    """
    Crea o actualiza el progreso de la actividad.
    Guarda el mejor puntaje (incluso en derrota, RN-18) y actualiza intentos.
    """
    from django.utils import timezone
    from login.models import Usuario

    if hasattr(usuario_cuenta, "usuario"):
        usuario = usuario_cuenta.usuario
    else:
        usuario, _ = Usuario.objects.get_or_create(
            cuenta=usuario_cuenta,
            defaults={
                "nombre": usuario_cuenta.get_full_name() or usuario_cuenta.get_username(),
                "email": usuario_cuenta.email,
            },
        )

    obj, created = ProgresoActividad.objects.get_or_create(
        actividad=actividad,
        usuario=usuario,
        defaults={
            "estado": "completado" if completada else "en_progreso",
            "puntaje": puntaje,
            "intentos": 1,
            "fecha_inicio": timezone.now(),
            "fecha_completado": timezone.now() if completada else None,
        },
    )
    if not created:
        obj.intentos += 1
        obj.puntaje = max(obj.puntaje, puntaje)
        if completada:
            obj.estado = "completado"
            obj.fecha_completado = timezone.now()
        obj.save(update_fields=["intentos", "puntaje", "estado", "fecha_completado"])
    return obj


def _desbloquear_siguiente(actividad, usuario_cuenta):
    """
    Desbloquea la siguiente actividad del temario cuando se completa la actual.
    """
    from django.utils import timezone
    from login.models import Usuario

    if hasattr(usuario_cuenta, "usuario"):
        usuario = usuario_cuenta.usuario
    else:
        usuario, _ = Usuario.objects.get_or_create(
            cuenta=usuario_cuenta,
            defaults={
                "nombre": usuario_cuenta.get_full_name() or usuario_cuenta.get_username(),
                "email": usuario_cuenta.email,
            },
        )

    siguiente = (
        Actividad.objects
        .filter(temario=actividad.temario, orden__gt=actividad.orden)
        .order_by("orden")
        .first()
    )
    if siguiente is None:
        return False

    ProgresoActividad.objects.get_or_create(
        actividad=siguiente,
        usuario=usuario,
        defaults={
            "estado": "disponible",
            "puntaje": 0,
            "intentos": 0,
            "fecha_inicio": timezone.now(),
        },
    )
    return True


# ----------------------------------------------------------------------
# Vista principal: GET /snake/<actividad_id>/
# ----------------------------------------------------------------------
@login_required
@require_GET
def vista_snake(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id)

    # Excepcion 1.0 del diagrama de secuencia: error en la carga del reto
    niveles = Snake.obtener_niveles(actividad_id)
    if niveles is not None:
        niveles = [n for n in niveles if n.items.count() > 0]

    if not niveles:
        messages.error(
            request,
            "No se pudieron recuperar los datos del juego de Snake. Intenta de nuevo más tarde."
        )
        return redirect(_url_temario(actividad))

    niveles_preparados = [Ops.preparar_nivel(n) for n in niveles]

    # Obtener el progreso actual del usuario si existe
    puntaje_previo = 0
    from login.models import Usuario
    usuario = getattr(request.user, "usuario", None) or Usuario.objects.filter(cuenta=request.user).first()
    if usuario:
        prog = ProgresoActividad.objects.filter(usuario=usuario, actividad=actividad).first()
        if prog:
            puntaje_previo = prog.puntaje

    return render(request, "snake.html", {
        "actividad": actividad,
        "niveles": niveles_preparados,
        "puntaje_previo": puntaje_previo,
        "url_temario": _url_temario(actividad),
    })


# ----------------------------------------------------------------------
# Finalizar partida: POST /snake/<actividad_id>/finalizar/
# ----------------------------------------------------------------------
@login_required
@require_POST
def finalizar_partida(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id)
    datos = _datos(request)

    nivel_id = datos.get("nivel_id")
    objetivos_recolectados = datos.get("objetivos_recolectados", 0)
    motivo_fin = datos.get("motivo_fin", Ops.MOTIVO_CHOQUE_MURO)
    segundos = datos.get("segundos", 0)

    try:
        nivel = NivelSnake.objects.prefetch_related("items").get(pk=nivel_id, snake_id=actividad_id)
    except NivelSnake.DoesNotExist:
        return JsonResponse({"error": "nivel_no_existe"}, status=404)
    except DatabaseError:
        return JsonResponse({"error": "bd_error"}, status=503)

    total_objetivos = nivel.items.filter(es_objetivo=True).count()

    if not Ops.validar_resultado(objetivos_recolectados, total_objetivos):
        return JsonResponse({"error": "datos_invalidos"}, status=400)

    puntaje_obtenido = Ops.calcular_puntaje(objetivos_recolectados, total_objetivos)
    es_victoria = (
        objetivos_recolectados >= total_objetivos
        and motivo_fin == Ops.MOTIVO_TODOS_OBJETIVOS
    )

    desbloqueada = False
    try:
        with transaction.atomic():
            progreso = _guardar_progreso(actividad, request.user, puntaje_obtenido, es_victoria)
            if es_victoria:
                desbloqueada = _desbloquear_siguiente(actividad, request.user)
    except DatabaseError:
        return JsonResponse({"error": "bd_error"}, status=503)

    return JsonResponse({
        "puntaje": puntaje_obtenido,
        "mejor_puntaje": progreso.puntaje,
        "estado": progreso.estado,
        "intentos": progreso.intentos,
        "es_victoria": es_victoria,
        "desbloqueada": desbloqueada,
        "motivo_fin": motivo_fin,
        "objetivos_recolectados": objetivos_recolectados,
        "total_objetivos": total_objetivos,
        "segundos": segundos,
    })
