from django.db import models
from contenido.models import Actividad

# Create your models here.
class Memorama(models.Model):
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="memorama",
    )  # columna: actividad_id (PK, FK)

    class Meta:
        db_table = "memorama"

    def __str__(self):
        return f"Memorama: {self.actividad}"

class Par(models.Model):
    id = models.AutoField(primary_key=True)
    memorama = models.ForeignKey(
        Memorama, on_delete=models.CASCADE, related_name="pares"
    )  # columna: memorama_id
    elemento_a = models.CharField(max_length=200)
    elemento_b = models.CharField(max_length=200)

    class Meta:
        db_table = "par"

    @classmethod
    def todos_los_pares(cls, id_memorama=None):
        if id_memorama is None:
            return []
        return list(cls.objects.filter(memorama_id=id_memorama))

    def __str__(self):
        return f"{self.elemento_a} <-> {self.elemento_b}"