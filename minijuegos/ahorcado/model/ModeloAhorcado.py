from django.db import models, DatabaseError
from contenido.models import Actividad


class AhorcadoJuego(models.Model):
    """
    Especialización 1:0..1 de ACTIVIDAD ("es un").
    Representa la configuración del juego del ahorcado para una actividad.
    """
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='actividad_id',
        related_name='ahorcado_juego'
    )

    class Meta:
        db_table = 'ahorcado_juego'
        verbose_name = 'Juego del Ahorcado'
        verbose_name_plural = 'Juegos del Ahorcado'

    def __str__(self):
        return f"Ahorcado: {self.actividad.titulo if self.actividad else self.actividad_id}"


class PalabraAhorcado(models.Model):
    """
    Palabra perteneciente a un juego de ahorcado.
    Contiene la palabra oculta, la pista inicial (paso 5) y cuántas letras se exponen al inicio (paso 4).
    """
    id = models.AutoField(primary_key=True)
    ahorcado = models.ForeignKey(
        AhorcadoJuego,
        on_delete=models.CASCADE,
        db_column='ahorcado_id',
        related_name='palabras'
    )
    palabra = models.CharField(max_length=100)
    pista_inicial = models.CharField(max_length=255)
    letras_expuestas = models.IntegerField(default=1)

    class Meta:
        db_table = 'palabra_ahorcado'
        verbose_name = 'Palabra de Ahorcado'
        verbose_name_plural = 'Palabras de Ahorcado'

    def __str__(self):
        return f"{self.palabra} (Ahorcado #{self.ahorcado_id})"


class PistaAhorcado(models.Model):
    """
    Pistas adicionales para cada palabra.
    Se entregan en orden ascendente de 'orden', máximo 3 (flujo 1.2).
    """
    id = models.AutoField(primary_key=True)
    palabra = models.ForeignKey(
        PalabraAhorcado,
        on_delete=models.CASCADE,
        db_column='palabra_id',
        related_name='pistas'
    )
    texto = models.CharField(max_length=255)
    orden = models.IntegerField(default=1)

    class Meta:
        db_table = 'pista_ahorcado'
        ordering = ['orden']
        verbose_name = 'Pista de Ahorcado'
        verbose_name_plural = 'Pistas de Ahorcado'

    def __str__(self):
        return f"Pista {self.orden} [{self.palabra.palabra}]: {self.texto}"


class ModeloAhorcado:
    """
    Capa de acceso a datos para el Ahorcado (Pasos 5 y 6 del diagrama).
    """

    @classmethod
    def obtenerPalabraActual(cls, id_ahorcado, palabra_id=None):
        """
        # Pasos 5 y 6: Consulta PALABRA_AHORCADO junto con sus PISTA_AHORCADO.
        Retorna una tupla (PalabraAhorcado, list[PistaAhorcado]) o None si no hay
        palabras o si ocurre un error de base de datos/timeout (Excepción 1.0.E1).
        """
        try:
            qs = PalabraAhorcado.objects.filter(ahorcado_id=id_ahorcado).prefetch_related('pistas')
            if not qs.exists():
                return None

            if palabra_id:
                palabra_obj = qs.filter(id=palabra_id).first()
            else:
                palabra_obj = qs.order_by('id').first()

            if not palabra_obj:
                return None

            # Máximo 3 pistas ordenadas por orden ascendente (flujo 1.2)
            pistas = list(palabra_obj.pistas.order_by('orden')[:3])
            return palabra_obj, pistas
        except DatabaseError:
            return None
        except Exception:
            return None

