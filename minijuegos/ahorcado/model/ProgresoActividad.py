from django.db import models, DatabaseError
from django.utils import timezone
from login.models import Usuario
from contenido.models import Actividad


class ProgresoActividad(models.Model):
    """
    Tabla de resultados: PROGRESO_ACTIVIDAD.
    Relación USUARIO 'registra' (1:N) y ACTIVIDAD 'es_evaluada_en' (1:N).
    Mapeada como managed = False pues la tabla pertenece al esquema base de la plataforma.
    Valores permitidos de estado: 'en_progreso', 'completada', 'no_completada'.
    """
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='usuario_id',
        related_name='progresos_ahorcado_mini'
    )
    actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        db_column='actividad_id',
        related_name='progresos_ahorcado_mini'
    )
    estado = models.CharField(max_length=30)
    puntaje = models.IntegerField(default=0)
    intentos = models.IntegerField(default=0)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'progreso_actividad'
        managed = False
        verbose_name = 'Progreso de Actividad'
        verbose_name_plural = 'Progresos de Actividades'

    def __str__(self):
        return f"{self.usuario_id} - {self.actividad_id} ({self.estado}) [Intentos: {self.intentos}]"

    @classmethod
    def guardarProgresoActividad(cls, id_usuario, id_actividad, resultado):
        """
        # Pasos 24-25 y 31-32 del diagrama de secuencia.
        Hace INSERT o UPDATE en PROGRESO_ACTIVIDAD (un registro por usuario y actividad;
        si ya existe, actualiza y suma a intentos si inicia partida o si se especifica).
        
        resultado: dict con claves opcionales:
          - 'estado': 'en_progreso', 'completada', 'no_completada'
          - 'puntaje': int
          - 'fecha_inicio': datetime
          - 'fecha_completado': datetime
          - 'sumar_intento': bool (True al iniciar partida para incrementar intentos)
        """
        try:
            progreso = cls.objects.filter(usuario_id=id_usuario, actividad_id=id_actividad).first()
            ahora = timezone.now()

            if not progreso:
                progreso = cls(
                    usuario_id=id_usuario,
                    actividad_id=id_actividad,
                    estado=resultado.get('estado', 'en_progreso'),
                    puntaje=resultado.get('puntaje', 0),
                    intentos=resultado.get('intentos', 1),
                    fecha_inicio=resultado.get('fecha_inicio', ahora),
                    fecha_completado=resultado.get('fecha_completado', None)
                )
            else:
                if 'estado' in resultado and resultado['estado']:
                    progreso.estado = resultado['estado']

                if 'puntaje' in resultado and resultado['puntaje'] is not None:
                    progreso.puntaje = resultado['puntaje']

                if resultado.get('sumar_intento', False):
                    progreso.intentos = (progreso.intentos or 0) + 1
                elif 'intentos' in resultado:
                    progreso.intentos = resultado['intentos']

                if 'fecha_inicio' in resultado and resultado['fecha_inicio']:
                    progreso.fecha_inicio = resultado['fecha_inicio']

                if 'fecha_completado' in resultado:
                    progreso.fecha_completado = resultado['fecha_completado']

            progreso.save()
            return progreso
        except DatabaseError:
            return None
        except Exception:
            return None

