from django.db import models, DatabaseError
from contenido.models import Actividad


class TipoConcepto(models.TextChoices):
    POSITIVO = 'positivo', 'Positivo'
    NEGATIVO = 'negativo', 'Negativo'


class CodeBreaker(models.Model):
    """
    Entidad principal de CodeBreaker vinculada 1:1 con Actividad.
    RN-96: Consta de 60 bloques (6 filas x 10 columnas) con 8 bloques especiales.
    """
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="codebreaker"
    )
    filas = models.PositiveIntegerField(default=6)
    columnas = models.PositiveIntegerField(default=10)
    bloques_totales = models.PositiveIntegerField(default=60)
    bloques_especiales = models.PositiveIntegerField(default=8)

    class Meta:
        db_table = "codebreaker"

    def __str__(self):
        return f"CodeBreaker: {self.actividad.titulo if self.actividad else self.pk}"

    @classmethod
    def obtener_codebreaker(cls, actividad_id):
        """
        Retorna la instancia de CodeBreaker pre-cargando los conceptos asociados.
        Devuelve None ante excepción o si no existe (Excepción 1.0.E1).
        """
        try:
            return cls.objects.prefetch_related("conceptos").get(pk=actividad_id)
        except (cls.DoesNotExist, DatabaseError):
            return None


class ConceptoCodeBreaker(models.Model):
    """
    Concepto pedagógico asociado a un bloque especial.
    RN-96 y RN-97: 8 conceptos (6 positivos y 2 negativos), cada uno con definición,
    explicación, tipo, efecto y ejemplo o aplicación registrados.
    """
    id = models.AutoField(primary_key=True)
    codebreaker = models.ForeignKey(
        CodeBreaker,
        on_delete=models.CASCADE,
        related_name="conceptos"
    )
    nombre = models.CharField(max_length=100)
    nombre_corto = models.CharField(max_length=30)
    tipo = models.CharField(
        max_length=20,
        choices=TipoConcepto.choices,
        default=TipoConcepto.POSITIVO
    )
    efecto_clave = models.CharField(max_length=30)
    efecto_descripcion = models.CharField(max_length=255)
    definicion = models.TextField()
    explicacion = models.TextField()
    tipo_ejemplo = models.CharField(max_length=50, default="Ejemplo")
    ejemplo = models.TextField()
    color = models.CharField(max_length=20, default="#5b5bf0")

    class Meta:
        db_table = "concepto_codebreaker"
        ordering = ["id"]

    def __str__(self):
        return f"[{self.tipo.upper()}] {self.nombre} ({self.efecto_clave})"

    def to_dict(self):
        """Serialización para el motor de juego en el frontend."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "es_positivo": self.tipo == TipoConcepto.POSITIVO,
            "nombre_corto": self.nombre_corto,
            "efecto_clave": self.efecto_clave,
            "efecto_descripcion": self.efecto_descripcion,
            "definicion": self.definicion,
            "explicacion": self.explicacion,
            "tipo_ejemplo": self.tipo_ejemplo,
            "ejemplo": self.ejemplo,
            "color": self.color,
        }
