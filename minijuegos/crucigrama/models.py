from django.db import models, DatabaseError
from contenido.models import Actividad


class Crucigrama(models.Model):
    """
    Modelo principal del crucigrama. Se vincula 1:1 con una Actividad.
    Corresponde a la entidad CRUCIGRAMA del diagrama de BD.
    """
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="crucigrama"
    )
    filas = models.PositiveIntegerField(default=13)
    columnas = models.PositiveIntegerField(default=10)
    tiempo_limite_seg = models.PositiveIntegerField(default=180)

    class Meta:
        db_table = "crucigrama"

    def __str__(self):
        return f"Crucigrama: {self.actividad.titulo if self.actividad else self.pk}"

    @classmethod
    def obtener_crucigrama(cls, actividad_id):
        """
        Retorna el crucigrama con sus palabras para la actividad especificada.
        Devuelve None si ocurre un error de base de datos.
        """
        try:
            return cls.objects.prefetch_related("palabras").get(pk=actividad_id)
        except cls.DoesNotExist:
            return None
        except DatabaseError:
            return None


class PalabraCrucigrama(models.Model):
    """
    Cada palabra del crucigrama con su posición, dirección y contenido.
    Corresponde a la entidad PALABRA_CRUCIGRAMA del diagrama de BD.
    """
    DIRECCION_HORIZONTAL = 'h'
    DIRECCION_VERTICAL = 'v'
    DIRECCION_CHOICES = [
        (DIRECCION_HORIZONTAL, 'Horizontal'),
        (DIRECCION_VERTICAL, 'Vertical'),
    ]

    id = models.AutoField(primary_key=True)
    crucigrama = models.ForeignKey(
        Crucigrama,
        on_delete=models.CASCADE,
        related_name="palabras"
    )
    numero = models.PositiveIntegerField()
    direccion = models.CharField(max_length=1, choices=DIRECCION_CHOICES)
    fila_inicio = models.PositiveIntegerField()
    columna_inicio = models.PositiveIntegerField()
    respuesta = models.CharField(max_length=50)
    enunciado = models.TextField()
    explicacion = models.TextField()

    class Meta:
        db_table = "palabra_crucigrama"
        ordering = ["numero"]

    def __str__(self):
        dir_txt = "H" if self.direccion == self.DIRECCION_HORIZONTAL else "V"
        return f"{self.numero}{dir_txt}: {self.respuesta}"
