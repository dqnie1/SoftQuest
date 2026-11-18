import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from contenido.models import Actividad, ProgresoActividad
from .models import Crucigrama, PalabraCrucigrama
from .operaciones.OperacionesCrucigrama import OperacionesCrucigrama as Ops


# ----------------------------------------------------------------------
# Utilidades de navegación y progreso
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
    Guarda el mejor puntaje y actualiza intentos.
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
    RN-66: Desbloquea la siguiente actividad del temario cuando se completa la actual.
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
# Vista principal: GET /crucigrama/<actividad_id>/
# ----------------------------------------------------------------------
@login_required
@require_GET
def vista_crucigrama(request, actividad_id):
    """
    CU-09 Flujo Normal paso 1: Recupera el crucigrama de la actividad.
    Excepción 1.0.E1: Si no se pueden cargar los datos, redirige al temario.
    """
    actividad = get_object_or_404(Actividad, pk=actividad_id)

    # Excepción 1.0.E1: Error en la carga del crucigrama
    crucigrama = Crucigrama.obtener_crucigrama(actividad_id)

    if crucigrama is None or crucigrama.palabras.count() == 0:
        messages.error(
            request,
            "No se pudieron recuperar los datos del crucigrama. Intenta de nuevo más tarde."
        )
        return redirect(_url_temario(actividad))

    datos_crucigrama = Ops.preparar_crucigrama(crucigrama)

    # Obtener el progreso actual del usuario si existe
    puntaje_previo = 0
    from login.models import Usuario
    usuario = getattr(request.user, "usuario", None) or Usuario.objects.filter(
        cuenta=request.user
    ).first()
    if usuario:
        prog = ProgresoActividad.objects.filter(
            usuario=usuario, actividad=actividad
        ).first()
        if prog:
            puntaje_previo = prog.puntaje

    return render(request, "crucigrama.html", {
        "actividad": actividad,
        "crucigrama": datos_crucigrama,
        "puntaje_previo": puntaje_previo,
        "url_temario": _url_temario(actividad),
    })


# ----------------------------------------------------------------------
# Finalizar partida: POST /crucigrama/<actividad_id>/finalizar/
# ----------------------------------------------------------------------
@login_required
@require_POST
def finalizar_partida(request, actividad_id):
    """
    Registra el resultado del crucigrama.
    Calcula XP según RN-64, RN-65.
    Desbloquea siguiente actividad según RN-66.
    """
    actividad = get_object_or_404(Actividad, pk=actividad_id)
    datos = _datos(request)

    palabras_resueltas = datos.get("palabras_resueltas", 0)
    palabras_primer_intento = datos.get("palabras_primer_intento", 0)
    vidas_restantes = datos.get("vidas_restantes", 0)
    vidas_perdidas = datos.get("vidas_perdidas", 0)
    tiempo_empleado = datos.get("tiempo_empleado", 0)
    completado = datos.get("completado", False)

    try:
        crucigrama = Crucigrama.objects.prefetch_related("palabras").get(pk=actividad_id)
    except Crucigrama.DoesNotExist:
        return JsonResponse({"error": "crucigrama_no_existe"}, status=404)
    except DatabaseError:
        return JsonResponse({"error": "bd_error"}, status=503)

    total_palabras = crucigrama.palabras.count()

    if not Ops.validar_resultado(palabras_resueltas, total_palabras, vidas_restantes):
        return JsonResponse({"error": "datos_invalidos"}, status=400)

    puntaje_obtenido = Ops.calcular_xp(palabras_primer_intento, total_palabras)
    es_completado = completado and (palabras_resueltas >= total_palabras)

    desbloqueada = False
    try:
        with transaction.atomic():
            progreso = _guardar_progreso(actividad, request.user, puntaje_obtenido, es_completado)
            if es_completado:
                desbloqueada = _desbloquear_siguiente(actividad, request.user)
    except DatabaseError:
        return JsonResponse({"error": "bd_error"}, status=503)

    return JsonResponse({
        "puntaje": puntaje_obtenido,
        "mejor_puntaje": progreso.puntaje,
        "estado": progreso.estado,
        "intentos": progreso.intentos,
        "completado": es_completado,
        "desbloqueada": desbloqueada,
        "palabras_resueltas": palabras_resueltas,
        "total_palabras": total_palabras,
        "palabras_primer_intento": palabras_primer_intento,
        "vidas_perdidas": vidas_perdidas,
        "tiempo_empleado": tiempo_empleado,
    })
