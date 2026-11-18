from django.db import models, DatabaseError
from contenido.models import Actividad


class SopaLetras(models.Model):
    """
    Entidad principal de Sopa de Letras vinculada 1:1 con Actividad.
    RN-81: Consta de una sola sopa de letras de 12x12 con 8 palabras.
    """
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="sopaletras"
    )
    dimension = models.PositiveIntegerField(default=12)
    total_palabras = models.PositiveIntegerField(default=8)

    class Meta:
        db_table = "sopa_letras"

    def __str__(self):
        return f"Sopa de Letras: {self.actividad.titulo if self.actividad else self.pk}"

    @classmethod
    def obtener_sopa_letras(cls, actividad_id):
        """
        Retorna la instancia de SopaLetras pre-cargando sus palabras.
        Devuelve None ante error de base de datos o si no existe (Excepción 1.0.E1).
        """
        try:
            return cls.objects.prefetch_related("palabras").get(pk=actividad_id)
        except (cls.DoesNotExist, DatabaseError):
            return None


class PalabraSopa(models.Model):
    """
    Palabra y concepto pedagógico a encontrar en la cuadrícula.
    RN-81 y RN-83: 8 palabras en mayúsculas y sin acentos, con definición, explicación y ejemplo.
    """
    id = models.AutoField(primary_key=True)
    sopaletras = models.ForeignKey(
        SopaLetras,
        on_delete=models.CASCADE,
        related_name="palabras"
    )
    palabra = models.CharField(max_length=50)
    nombre = models.CharField(max_length=50)
    definicion = models.TextField()
    explicacion = models.TextField()
    tipo_ejemplo = models.CharField(max_length=50, default="Ejemplo")
    ejemplo = models.TextField()
    color = models.CharField(max_length=20, default="#818cf8")

    class Meta:
        db_table = "palabra_sopa"
        ordering = ["id"]

    def __str__(self):
        return f"{self.palabra} ({self.nombre})"

    def to_dict(self):
        """Serialización para el generador y evaluador de la sopa de letras en el frontend."""
        return {
            "id": self.id,
            "w": self.palabra.upper(),
            "n": self.nombre,
            "d": self.definicion,
            "e": self.explicacion,
            "k": self.tipo_ejemplo,
            "x": self.ejemplo,
            "color": self.color,
        }
