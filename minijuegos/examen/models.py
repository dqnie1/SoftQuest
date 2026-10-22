from django.db import models
from contenido.models import Mundo
from login.models import Usuario


class IntentoExamen(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="intentos_examen"
    )
    mundo = models.ForeignKey(
        Mundo, on_delete=models.CASCADE, related_name="intentos_examen"
    )
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    aprobado = models.BooleanField(default=False)
    tiempo_empleado_segundos = models.IntegerField(default=0)
    resultado_bloques = models.JSONField(default=dict)
    detalles_reactivos = models.JSONField(default=list)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "intento_examen"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        estado = "Aprobado" if self.aprobado else "No aprobado"
        return f"Intento {self.id} - {self.usuario} - {self.mundo.nombre} ({self.calificacion}% - {estado})"
