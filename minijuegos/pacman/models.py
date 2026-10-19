from django.db import models, DatabaseError
from contenido.models import Actividad

# Create your models here.

# ---------------------------------------------------------------------------
# PACMAN
# ---------------------------------------------------------------------------
class Pacman(models.Model):
    actividad = models.OneToOneField(Actividad, on_delete=models.CASCADE, primary_key=True, related_name="pacman")

    class Meta:
        db_table = "pacman"

    # obtenerNiveles(actividad_id)  -> SELECT * FROM PACMAN ...
    @classmethod
    def obtener_niveles(cls, actividad_id):
        """Niveles (con sus líneas) de la actividad. Devuelve None si la BD falla o da timeout."""
        try:
            return list(
                PacmanNivel.objects.filter(pacman_id=actividad_id)
                .order_by("orden")
                .prefetch_related("lineas")
            )
        except DatabaseError:  # OperationalError (TimeOut) hereda de DatabaseError
            return None


class PacmanNivel(models.Model):
    pacman = models.ForeignKey(Pacman, on_delete=models.CASCADE, related_name="niveles")
    orden = models.PositiveIntegerField(default=1)
    titulo = models.CharField(max_length=150)
    salida = models.TextField(blank=True)
    num_enemigos = models.PositiveIntegerField(default=1)
    velocidad_ms = models.PositiveIntegerField(default=560)

    class Meta:
        db_table = "pacman_nivel"
        ordering = ["orden"]

    def __str__(self):
        return self.titulo


class PacmanLinea(models.Model):
    nivel = models.ForeignKey(PacmanNivel, on_delete=models.CASCADE, related_name="lineas")
    orden = models.PositiveIntegerField()
    codigo = models.CharField(max_length=200)  # conserva la sangría (espacios al inicio)
    explicacion = models.TextField()           # admite <b>…</b>
    pista = models.CharField(max_length=250)
    concepto = models.CharField(max_length=100, blank=True)
    puntos = models.PositiveIntegerField(default=100)

    class Meta:
        db_table = "pacman_linea"
        ordering = ["orden"]

    def __str__(self):
        return f"{self.nivel_id}.{self.orden} {self.codigo.strip()}"