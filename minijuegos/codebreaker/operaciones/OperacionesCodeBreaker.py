from django.utils import timezone
from django.db import DatabaseError, transaction

from contenido.models import Actividad, ProgresoActividad
from login.models import Usuario
from ..models import CodeBreaker, ConceptoCodeBreaker


class OperacionesCodeBreaker:
    """
    Capa de operaciones y lógica del negocio para CU-11 Jugar CodeBreaker.
    """

    @staticmethod
    def obtener_codebreaker(actividad_id):
        """
        Recupera el juego CodeBreaker con sus conceptos.
        Retorna None ante error de base de datos o si no existe (Excepción 1.0.E1).
        """
        return CodeBreaker.obtener_codebreaker(actividad_id)

    @staticmethod
    def obtener_conceptos(codebreaker):
        """
        Retorna la lista de conceptos serializados para el frontend.
        """
        if not codebreaker:
            return []
        return [c.to_dict() for c in codebreaker.conceptos.all()]

    @staticmethod
    def calcular_xp(vidas_perdidas: int, completada: bool) -> int:
        """
        RN-111: El máximo de score obtenido es de 100. Cada vida perdida descuenta 10 XP.
        El XP solo se otorga al completar la actividad (si no se completa, 0 XP, RN-107).
        """
        if not completada:
            return 0
        vidas_perdidas = max(0, min(3, int(vidas_perdidas or 0)))
        return max(0, 100 - (10 * vidas_perdidas))

    @classmethod
    def registrar_resultado(
        cls,
        actividad: Actividad,
        usuario_cuenta,
        vidas_perdidas: int,
        conceptos_ids: list,
        completada: bool
    ) -> dict:
        """
        RN-108, RN-111, RN-113: Registra el resultado de la partida:
        - conceptos recolectados y vidas perdidas
        - progreso de la actividad (estado, puntaje XP, intentos, fecha)
        - si completada: desbloquea la siguiente actividad en el temario
        """
        xp = cls.calcular_xp(vidas_perdidas, completada)

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
            "vidas_perdidas": vidas_perdidas,
            "conceptos_recolectados": len(conceptos_ids or []),
            "siguiente_desbloqueada": siguiente_desbloqueada,
        }

    @staticmethod
    def desbloquear_siguiente(actividad: Actividad, usuario: Usuario) -> bool:
        """
        RN-108: Al completar la actividad se habilita la siguiente actividad del temario.
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
