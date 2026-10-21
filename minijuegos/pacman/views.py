import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET, require_POST

from contenido.models import Actividad, ProgresoActividad
from .models import Pacman, PacmanNivel
from .operaciones.OperacionesPacman import OperacionesPacman as Ops

SESSION_KEY = "pacman_juegos"


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def _url_temario(actividad):
    """Devuelve la URL del temario de la actividad, o '/' si no existe la ruta."""
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


def _juego(request, actividad_id):
    return request.session.get(SESSION_KEY, {}).get(str(actividad_id))


def _guardar_juego(request, actividad_id, juego):
    juegos = request.session.get(SESSION_KEY, {})
    juegos[str(actividad_id)] = juego
    request.session[SESSION_KEY] = juegos
    request.session.modified = True


def _error(codigo, status):
    return JsonResponse({"error": codigo}, status=status)


def _estado_activo(request, actividad_id):
    """Devuelve (juego, estado_del_nivel) o (None, None) si no hay partida en curso."""
    juego = _juego(request, actividad_id)
    if not juego or not juego.get("nivel") or juego["nivel"]["finalizado"]:
        return None, None
    return juego, juego["nivel"]


# ----------------------------------------------------------------------
# GET /pacman/<actividad_id>/
# ----------------------------------------------------------------------
@login_required
@require_GET
def vista_pacman(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id, tipo="pacman")

    niveles = Pacman.obtener_niveles(actividad_id)
    if niveles is not None:
        niveles = [n for n in niveles if len(n.lineas.all()) > 0]

    if not niveles:
        messages.error(request, "No se pudieron recuperar las lineas del reto. Intenta de nuevo mas tarde.")
        return redirect(_url_temario(actividad))

    mapa = Ops.mapa_aleatorio()
    _guardar_juego(request, actividad_id, Ops.nuevo_juego([n.id for n in niveles], mapa))

    return render(request, "pacman.html", {
        "actividad": actividad,
        "niveles": [Ops.preparar_nivel(n, mapa) for n in niveles],
        "mapa": mapa,
        "url_temario": _url_temario(actividad),
    })


# ----------------------------------------------------------------------
# POST /pacman/<actividad_id>/iniciar/
# ----------------------------------------------------------------------
@login_required
@require_POST
def iniciar_nivel(request, actividad_id):
    juego = _juego(request, actividad_id)
    if juego is None:
        return _error("sin_estado", 409)

    datos = _datos(request)
    try:
        nivel_id = int(datos.get("nivel_id"))
    except (TypeError, ValueError):
        nivel_id = None

    niveles_ids = [int(nid) for nid in juego.get("niveles", [])]
    if nivel_id not in niveles_ids:
        return _error("nivel_invalido", 400)

    try:
        nivel = PacmanNivel.objects.prefetch_related("lineas").get(pk=nivel_id, pacman_id=actividad_id)
    except PacmanNivel.DoesNotExist:
        return _error("nivel_no_existe", 404)
    except DatabaseError:
        return _error("bd", 503)

    estado = Ops.iniciar_nivel(juego, nivel, nuevo_juego=bool(datos.get("nuevo_juego")))
    _guardar_juego(request, actividad_id, juego)
    return JsonResponse({
        "vidas": estado["vidas"],
        "puntaje": estado["puntaje"],
        "siguiente": Ops.siguiente(estado),
    })


# ----------------------------------------------------------------------
# POST /pacman/<actividad_id>/recoger/  — validarOrdenFragmento
# ----------------------------------------------------------------------
@login_required
@require_POST
def recoger_linea(request, actividad_id):
    juego, estado = _estado_activo(request, actividad_id)
    if estado is None or estado["vidas"] <= 0:
        return _error("sin_estado", 409)

    linea_id = _datos(request).get("linea_id")

    if not Ops.validar_orden_fragmento(estado, linea_id):
        return JsonResponse({"correcto": False, "siguiente": Ops.siguiente(estado)})

    linea = Ops.registrar_fragmento(estado)
    _guardar_juego(request, actividad_id, juego)
    siguiente = Ops.siguiente(estado)
    return JsonResponse({
        "correcto": True,
        "explicacion": linea["explicacion"],
        "puntos": linea["puntos"],
        "puntaje": estado["puntaje"],
        "siguiente": siguiente,
        "completado": siguiente is None,
    })


# ----------------------------------------------------------------------
# POST /pacman/<actividad_id>/bug/  — un bug alcanza al jugador
# ----------------------------------------------------------------------
@login_required
@require_POST
def bug_alcanzo(request, actividad_id):
    juego, estado = _estado_activo(request, actividad_id)
    if estado is None or estado["vidas"] <= 0:
        return _error("sin_estado", 409)

    vidas = Ops.quitar_vida(estado)
    if vidas <= 0:
        _guardar_juego(request, actividad_id, juego)
        return JsonResponse({"vidas": 0, "game_over": True, "puntaje": estado["puntaje"]})

    devuelta = Ops.devolver_fragmento_al_tablero(estado)
    _guardar_juego(request, actividad_id, juego)
    return JsonResponse({
        "vidas": vidas,
        "game_over": False,
        "devuelta": devuelta,
        "puntaje": estado["puntaje"],
        "siguiente": Ops.siguiente(estado),
    })


# ----------------------------------------------------------------------
# POST /pacman/<actividad_id>/finalizar/  — ultimo fragmento, guardar progreso
# ----------------------------------------------------------------------
@login_required
@require_POST
def finalizar_nivel(request, actividad_id):
    juego = _juego(request, actividad_id)
    if not juego or not juego.get("nivel"):
        return _error("sin_estado", 409)
    estado = juego["nivel"]

    if estado["finalizado"]:
        return JsonResponse(estado["final"])
    if Ops.siguiente(estado) is not None:
        return _error("faltan_lineas", 409)

    resumen = Ops.calcular_resumen_nivel(estado)
    es_ultimo = juego["niveles"][-1] == estado["id"]
    actividad = get_object_or_404(Actividad, pk=actividad_id)

    desbloqueada = False
    try:
        with transaction.atomic():
            _guardar_progreso(actividad, request.user, resumen["puntaje_total"], es_ultimo)
            if es_ultimo:
                desbloqueada = _desbloquear_siguiente(actividad, request.user)
    except DatabaseError:
        return _error("bd", 503)

    respuesta = {"resumen": resumen, "es_ultimo": es_ultimo, "desbloqueada": desbloqueada}
    estado["puntaje"] = resumen["puntaje_total"]
    estado["finalizado"] = True
    estado["final"] = respuesta
    juego["total"] = resumen["puntaje_total"]
    _guardar_juego(request, actividad_id, juego)
    return JsonResponse(respuesta)


# ----------------------------------------------------------------------
# Helpers de progreso (usan ProgresoActividad directamente)
# ----------------------------------------------------------------------
def _guardar_progreso(actividad, usuario_cuenta, puntaje, completada):
    """Crea o actualiza el registro de ProgresoActividad."""
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


def _desbloquear_siguiente(actividad, usuario_cuenta):
    """
    Marca la siguiente actividad del temario como 'disponible' en ProgresoActividad.
    Devuelve True si se desbloqueo algo, False si no habia siguiente.
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
