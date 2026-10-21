from django.db import models, DatabaseError
from contenido.models import Actividad


class Snake(models.Model):
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="snake"
    )

    class Meta:
        db_table = "snake"

    def __str__(self):
        return f"Snake: {self.actividad.titulo if self.actividad else self.pk}"

    @classmethod
    def obtener_niveles(cls, actividad_id):
        """
        Retorna la lista de niveles con sus ítems para la actividad especificada.
        Devuelve None si ocurre un error de base de datos o timeout.
        """
        try:
            return list(
                NivelSnake.objects.filter(snake_id=actividad_id)
                .order_by("numero")
                .prefetch_related("items")
            )
        except DatabaseError:
            return None


class NivelSnake(models.Model):
    snake = models.ForeignKey(Snake, on_delete=models.CASCADE, related_name="niveles")
    numero = models.PositiveIntegerField(default=1)
    titulo = models.CharField(max_length=150)
    tema = models.CharField(max_length=150, default="Requerimientos de Software")
    instrucciones = models.TextField()
    filas = models.PositiveIntegerField(default=26)
    columnas = models.PositiveIntegerField(default=26)
    velocidad_ms = models.PositiveIntegerField(default=170)

    class Meta:
        db_table = "nivel_snake"
        ordering = ["numero"]

    def __str__(self):
        return f"Nivel {self.numero}: {self.titulo}"


class ItemNivel(models.Model):
    nivel = models.ForeignKey(NivelSnake, on_delete=models.CASCADE, related_name="items")
    identificador = models.CharField(max_length=50)
    categoria = models.CharField(max_length=100)
    texto = models.TextField()
    es_objetivo = models.BooleanField(default=True)  # True = RNF (Objetivo), False = RF (Obstáculo)
    explicacion = models.TextField()
    contraste = models.TextField(blank=True, default="")

    class Meta:
        db_table = "item_nivel"

    def __str__(self):
        tipo = "RNF (Objetivo)" if self.es_objetivo else "RF (Obstáculo)"
        return f"[{self.identificador}] {tipo} - {self.categoria}"
