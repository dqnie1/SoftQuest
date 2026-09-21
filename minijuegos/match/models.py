from django.db import models
from contenido.models import Actividad
# Create your models here.
class MatchJuego(models.Model):
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="match_juego",
    )  # columna: actividad_id (PK, FK)

    class Meta:
        db_table = "match_juego"

    def __str__(self):
        return f"Match: {self.actividad}"

class Concepto(models.Model):
    id = models.AutoField(primary_key=True)
    match = models.ForeignKey(
        MatchJuego, on_delete=models.CASCADE, related_name="conceptos"
    )  # columna: match_id
    termino = models.CharField(max_length=200)
    definicion = models.CharField(max_length=500)

    class Meta:
        db_table = "concepto"

    def __str__(self):
        return self.termino

