from django.utils import timezone
from django.db import DatabaseError, transaction

from contenido.models import Actividad, ProgresoActividad
from login.models import Usuario
from ..models import SopaLetras, PalabraSopa


class OperacionesSopaLetras:
    """
    Capa de operaciones y lógica del negocio para CU-12 Resolver sopa de letras.
    """

    @staticmethod
    def obtener_sopa_letras(actividad_id):
        """
        Recupera la actividad de Sopa de Letras con sus palabras.
        Retorna None ante error de base de datos o si no existe (Excepción 1.0.E1).
        """
        return SopaLetras.obtener_sopa_letras(actividad_id)

    @staticmethod
    def obtener_palabras(sopaletras):
        """
        Retorna la lista de palabras serializadas para el frontend.
        """
        if not sopaletras:
            return []
        return [p.to_dict() for p in sopaletras.palabras.all()]

    @staticmethod
    def calcular_xp(errores: int, completada: bool) -> int:
        """
        RN-92: Cada error descuenta 5 XP, sin que el XP pueda ser menor a 0.
        Puntuación máxima 100 XP. Si no se completa la actividad, no se otorga XP (0).
        """
        if not completada:
            return 0
        errores = max(0, int(errores or 0))
        return max(0, 100 - (5 * errores))

    @classmethod
    def registrar_resultado(
        cls,
        actividad: Actividad,
        usuario_cuenta,
        errores: int,
        pista_usada: bool,
        tiempo_segundos: int,
        completada: bool
    ) -> dict:
        """
        POST-2, POST-3, RN-92, RN-93: Registra el resultado de la partida:
        - palabras encontradas, errores cometidos, uso de pista y tiempo empleado
        - progreso de la actividad (estado, puntaje XP, intentos, fecha)
        - si completada: desbloquea la siguiente actividad en el temario
        """
        xp = cls.calcular_xp(errores, completada)

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

        with transaction.atomic():
            progreso, created = ProgresoActividad.objects.get_or_create(
                actividad=actividad,
                usuario=usuario,
                defaults={
                    "estado": "completado" if completada else "en_progreso",
                    "puntaje": xp,
                    "intentos": 1,
                    "fecha_inicio": timezone.now(),
                    "fecha_completado": timezone.now() if completada else None,
                },
            )

            if not created:
                progreso.intentos += 1
                progreso.puntaje = max(progreso.puntaje, xp)
                if completada:
                    progreso.estado = "completado"
                    progreso.fecha_completado = timezone.now()
                progreso.save(update_fields=["intentos", "puntaje", "estado", "fecha_completado"])

            siguiente_desbloqueada = False
            if completada:
                siguiente_desbloqueada = cls.desbloquear_siguiente(actividad, usuario)

        return {
            "ok": True,
            "completada": completada,
            "xp": xp,
            "errores": errores,
            "pista_usada": pista_usada,
            "tiempo_segundos": tiempo_segundos,
            "siguiente_desbloqueada": siguiente_desbloqueada,
        }

    @staticmethod
    def desbloquear_siguiente(actividad: Actividad, usuario: Usuario) -> bool:
        """
        RN-93: La actividad se completa cuando el jugador encuentra las 8 palabras;
        al completarla se habilita la siguiente actividad del temario.
        """
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
