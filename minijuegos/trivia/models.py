from django.db import models
from contenido.models import Actividad

# Create your models here.
class Trivia(models.Model):
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="trivia",
    )  # columna: actividad_id (PK, FK)

    class Meta:
        db_table = "trivia"

    def __str__(self):
        return f"Trivia: {self.actividad}"


class Pregunta(models.Model):
    id = models.AutoField(primary_key=True)
    trivia = models.ForeignKey(
        Trivia, on_delete=models.CASCADE, related_name="preguntas"
    )  # columna: trivia_id
    texto = models.CharField(max_length=500)

    class Meta:
        db_table = "pregunta"

    def __str__(self):
        return self.texto

    @classmethod
    def todas_las_preguntas(cls, id_trivia=None):
        if id_trivia is None:
            return []
        return list(
            cls.objects.filter(trivia_id=id_trivia)
            .prefetch_related('respuestas')
            .order_by('id')
        )


class Respuesta(models.Model):
    id = models.AutoField(primary_key=True)
    pregunta = models.ForeignKey(
        Pregunta, on_delete=models.CASCADE, related_name="respuestas"
    )  # columna: pregunta_id
    texto = models.CharField(max_length=500)
    es_correcta = models.BooleanField(default=False)

    class Meta:
        db_table = "respuesta"

    def __str__(self):
        return self.texto
