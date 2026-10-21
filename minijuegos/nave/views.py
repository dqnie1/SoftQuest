import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from contenido.models import Actividad, ProgresoActividad
from contenido.operaciones.OperacionesContenido import OperacionesContenido
from login.models import Usuario
from .models import NaveEspacial
from .operaciones.OperacionesNave import EstadoPartida, OperacionesNave

SESSION_KEY = "nave_partidas"


def _url_temario(actividad):
    """Devuelve la URL del temario de la actividad, o mapa de mundos como fallback."""
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


def _obtener_usuario_perfil(usuario_auth):
    if hasattr(usuario_auth, "perfil_contenido") and usuario_auth.perfil_contenido:
        return usuario_auth.perfil_contenido
    usuario, _ = Usuario.objects.get_or_create(
        cuenta=usuario_auth,
        defaults={
            "nombre": usuario_auth.get_full_name() or usuario_auth.get_username(),
            "email": usuario_auth.email,
        },
    )
    return usuario


def _guardar_progreso(actividad, usuario_auth, puntaje, completada):
    usuario = _obtener_usuario_perfil(usuario_auth)
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


def _desbloquear_siguiente(actividad, usuario_auth):
    usuario = _obtener_usuario_perfil(usuario_auth)
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


class ViewNave:
    """Controlador principal para el caso de uso CU-06 Jugar Nave Espacial."""

    # Caché en memoria por proceso para eliminar consultas a base de datos durante la partida en tiempo real
    _CACHE_PARTIDAS = {}

    @classmethod
    def _cache_key(cls, request, actividad_id):
        uid = request.user.id if request.user and request.user.is_authenticated else "anon"
        return f"{uid}_{actividad_id}"

    @classmethod
    def obtener_partida(cls, request, actividad_id):
        key = cls._cache_key(request, actividad_id)
        if key in cls._CACHE_PARTIDAS:
            data = cls._CACHE_PARTIDAS[key]
            return data["estado"], data["banco_req"], data["banco_anom"]

        # Fallback a session
        partidas = request.session.get(SESSION_KEY, {})
        data = partidas.get(str(actividad_id))
        if not data:
            return None, None, None

        estado_raw = data.get("estado") if isinstance(data, dict) and "estado" in data else data
        estado = EstadoPartida.from_dict(estado_raw)
        banco_req = data.get("banco_req", {}) if isinstance(data, dict) else {}
        banco_anom = data.get("banco_anom", {}) if isinstance(data, dict) else {}

        cls._CACHE_PARTIDAS[key] = {
            "estado": estado,
            "banco_req": banco_req,
            "banco_anom": banco_anom,
        }
        return estado, banco_req, banco_anom

    @classmethod
    def guardar_partida(cls, request, actividad_id, estado, banco_req=None, banco_anom=None):
        """Escribe únicamente al caché en memoria. SIN escribir a la sesión de Django.
        Esto elimina la latencia de base de datos en cada disparo/penalización.
        Llama a flush_to_session() sólo al finalizar la partida."""
        key = cls._cache_key(request, actividad_id)
        entry = cls._CACHE_PARTIDAS.get(key, {})
        entry["estado"] = estado
        if banco_req is not None:
            entry["banco_req"] = banco_req
        if banco_anom is not None:
            entry["banco_anom"] = banco_anom
        cls._CACHE_PARTIDAS[key] = entry

    @classmethod
    def flush_to_session(cls, request, actividad_id, estado):
        """Persiste el estado final a la sesión de Django (una sola vez, al finalizar)."""
        key = cls._cache_key(request, actividad_id)
        entry = cls._CACHE_PARTIDAS.get(key, {})
        banco_req = entry.get("banco_req")
        banco_anom = entry.get("banco_anom")

        partidas = request.session.get(SESSION_KEY, {})
        cur = partidas.get(str(actividad_id), {})
        if not isinstance(cur, dict):
            cur = {}
        cur["estado"] = estado.to_dict()
        if banco_req is not None:
            cur["banco_req"] = banco_req
        if banco_anom is not None:
            cur["banco_anom"] = banco_anom
        partidas[str(actividad_id)] = cur
        request.session[SESSION_KEY] = partidas
        request.session.modified = True

    @classmethod
    def jugar(cls, request, actividad_id):
        actividad = get_object_or_404(Actividad, pk=actividad_id)
        try:
            nave = NaveEspacial.objects.prefetch_related(
                'requerimientos',
                'anomalias__opciones'
            ).get(actividad=actividad)
        except NaveEspacial.DoesNotExist:
            messages.error(request, "No se encontró la configuración de la nave para esta actividad.")
            return redirect(_url_temario(actividad))

        requerimientos = list(nave.requerimientos.all())
        anomalias = list(nave.anomalias.all())

        if not requerimientos:
            messages.error(request, "No fue posible cargar los requerimientos de la actividad.")
            return redirect(_url_temario(actividad))

        req_revueltos, anom_revueltas = OperacionesNave.revolverBanco(requerimientos, anomalias)
        estado = OperacionesNave.iniciarPartida()

        # Construir bancos en memoria para evitar consultas lentas a Neon durante cada disparo
        banco_req = {
            r.id: {
                "tipo": r.tipo,
                "explicacion": r.explicacion,
            }
            for r in requerimientos
        }
        banco_anom = {
            a.id: {
                "explicacion": a.explicacion,
                "opcion_correcta_id": next((o.id for o in a.opciones.all() if o.es_correcta), None),
            }
            for a in anomalias
        }

        cls.guardar_partida(request, actividad_id, estado, banco_req=banco_req, banco_anom=banco_anom)

        # Formato para el navegador: NUNCA enviar respuestas correctas ni explicaciones antes de tiempo
        requerimientos_payload = [
            {
                "id": r.id,
                "texto": r.texto,
                "text": r.texto,
            }
            for r in req_revueltos
        ]

        anomalias_payload = [
            {
                "id": a.id,
                "texto_ambiguo": a.texto_ambiguo,
                "vague": a.texto_ambiguo,
                "tiempo_limite_seg": a.tiempo_limite_seg,
                "opciones": [
                    {"id": o.id, "texto": o.texto, "text": o.texto}
                    for o in a.opciones.all()
                ],
            }
            for a in anom_revueltas
        ]

        context = {
            "actividad": actividad,
            "nave": nave,
            "requerimientos_json": json.dumps(requerimientos_payload),
            "anomalias_json": json.dumps(anomalias_payload),
            "estado": estado.to_dict(),
            "url_temario": _url_temario(actividad),
        }
        return render(request, "nave.html", context)

    @classmethod
    def iniciar_partida(cls, request, actividad_id):
        actividad = get_object_or_404(Actividad, pk=actividad_id)
        estado = OperacionesNave.iniciarPartida()
        cls.guardar_partida(request, actividad_id, estado)
        return JsonResponse({"ok": True, "estado": estado.to_dict()})

    @classmethod
    def clasificar(cls, request, actividad_id):
        estado, banco_req, _ = cls.obtener_partida(request, actividad_id)
        if not estado:
            return JsonResponse({"ok": False, "error": "No hay una partida iniciada."}, status=400)
        if estado.partida_terminada:
            return JsonResponse({"ok": False, "error": "La partida ya ha finalizado.", "estado": estado.to_dict()}, status=400)

        datos = _datos_json(request)
        tipo_laser = datos.get("tipo_laser")
        requerimiento_id = datos.get("requerimiento_id")

        if not tipo_laser or requerimiento_id is None:
            return JsonResponse({"ok": False, "error": "Faltan parámetros tipo_laser o requerimiento_id."}, status=400)

        # Validación instantánea sin consulta a base de datos
        correcto, explicacion, tipo_correcto, estado_actualizado = OperacionesNave.validarClasificacion(
            tipo_laser=tipo_laser,
            requerimiento_id=requerimiento_id,
            estado=estado,
            banco_req=banco_req
        )
        cls.guardar_partida(request, actividad_id, estado_actualizado)

        return JsonResponse({
            "ok": True,
            "correcto": correcto,
            "explicacion": explicacion,
            "tipo_correcto": tipo_correcto,
            "estado": estado_actualizado.to_dict(),
        })

    @classmethod
    def validar_metrica(cls, request, actividad_id):
        estado, _, banco_anom = cls.obtener_partida(request, actividad_id)
        if not estado:
            return JsonResponse({"ok": False, "error": "No hay una partida iniciada."}, status=400)
        if estado.partida_terminada:
            return JsonResponse({"ok": False, "error": "La partida ya ha finalizado.", "estado": estado.to_dict()}, status=400)

        datos = _datos_json(request)
        opcion_id = datos.get("opcion_id")
        anomalia_id = datos.get("anomalia_id")

        if opcion_id is None or anomalia_id is None:
            return JsonResponse({"ok": False, "error": "Faltan parámetros opcion_id o anomalia_id."}, status=400)

        # Validación instantánea sin consulta a base de datos
        correcta, explicacion, opcion_correcta_id, estado_actualizado = OperacionesNave.validarMetrica(
            opcion_id=opcion_id,
            anomalia_id=anomalia_id,
            estado=estado,
            banco_anom=banco_anom
        )
        cls.guardar_partida(request, actividad_id, estado_actualizado)

        return JsonResponse({
            "ok": True,
            "correcta": correcta,
            "explicacion": explicacion,
            "opcion_correcta_id": opcion_correcta_id,
            "estado": estado_actualizado.to_dict(),
        })

    @classmethod
    def penalizar(cls, request, actividad_id):
        estado, _, _ = cls.obtener_partida(request, actividad_id)
        if not estado:
            return JsonResponse({"ok": False, "error": "No hay una partida iniciada."}, status=400)
        if estado.partida_terminada:
            return JsonResponse({"ok": True, "estado": estado.to_dict()})

        datos = _datos_json(request)
        motivo = datos.get("motivo")

        try:
            estado_actualizado = OperacionesNave.penalizarEscudo(motivo=motivo, estado=estado)
        except ValueError as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

        cls.guardar_partida(request, actividad_id, estado_actualizado)
        return JsonResponse({
            "ok": True,
            "estado": estado_actualizado.to_dict(),
        })

    @classmethod
    def finalizar(cls, request, actividad_id):
        actividad = get_object_or_404(Actividad, pk=actividad_id)
        estado, banco_req, _ = cls.obtener_partida(request, actividad_id)
        if not estado:
            estado = OperacionesNave.iniciarPartida()

        estado.partida_terminada = True
        datos = _datos_json(request)
        requerimientos_generados = datos.get("requerimientos_generados", {})

        precision_data = OperacionesNave.calcularPrecision(estado, requerimientos_generados, banco_req=banco_req)
        xp = OperacionesNave.calcularXP(estado, precision_data["precision_global"])

        # RN-30 / RN-32: Registrar resultado y marcar completada
        _guardar_progreso(actividad, request.user, puntaje=xp, completada=True)

        # RN-33 / POST-3: Desbloquear siguiente si XP >= 70
        desbloqueada = False
        if xp >= OperacionesNave.UMBRAL_DESBLOQUEO:
            desbloqueada = _desbloquear_siguiente(actividad, request.user)

        # Actualizar progreso mundo si corresponde
        try:
            usuario_perfil = _obtener_usuario_perfil(request.user)
            OperacionesContenido().actualizar_progreso_mundo(usuario_perfil)
        except Exception:
            pass

        cls.flush_to_session(request, actividad_id, estado)

        return JsonResponse({
            "ok": True,
            "puntaje": estado.puntaje,
            "xp": xp,
            "precision_global": precision_data["precision_global"],
            "precision_rf": precision_data["precision_rf"],
            "precision_rnf": precision_data["precision_rnf"],
            "precision_rn": precision_data["precision_rn"],
            "aciertos_rf": estado.aciertos_rf,
            "aciertos_rnf": estado.aciertos_rnf,
            "aciertos_rn": estado.aciertos_rn,
            "total_aciertos": precision_data["total_aciertos"],
            "total_generados": precision_data["total_generados"],
            "siguiente_desbloqueada": desbloqueada,
            "url_temario": _url_temario(actividad),
            "estado": estado.to_dict(),
        })


# Funciones de vista expuestas para urls.py
@login_required
@require_GET
def vista_nave(request, actividad_id):
    return ViewNave.jugar(request, actividad_id)


@login_required
@require_POST
def iniciar_partida(request, actividad_id):
    return ViewNave.iniciar_partida(request, actividad_id)


@login_required
@require_POST
def clasificar_requerimiento(request, actividad_id):
    return ViewNave.clasificar(request, actividad_id)


@login_required
@require_POST
def validar_metrica(request, actividad_id):
    return ViewNave.validar_metrica(request, actividad_id)


@login_required
@require_POST
def penalizar_escudo(request, actividad_id):
    return ViewNave.penalizar(request, actividad_id)


@login_required
@require_POST
def finalizar_partida(request, actividad_id):
    return ViewNave.finalizar(request, actividad_id)
