from django.db import models
from contenido.models import Temario, Actividad, Mundo, ProgresoActividad, ProgresoUsuario, Usuario

# ---------------------------------------------------------------------------
# Especializaciones de ACTIVIDAD (PK = FK a Actividad)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Contenido de TRIVIA: PREGUNTA -> RESPUESTA
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Contenido de MATCH_JUEGO: CONCEPTO
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Contenido de MEMORAMA: PAR
# ---------------------------------------------------------------------------

class Par(models.Model):
    id = models.AutoField(primary_key=True)
    memorama = models.ForeignKey(
        Memorama, on_delete=models.CASCADE, related_name="pares"
    )  # columna: memorama_id
    elemento_a = models.CharField(max_length=200)
    elemento_b = models.CharField(max_length=200)

    class Meta:
        db_table = "par"

    def __str__(self):
        return f"{self.elemento_a} <-> {self.elemento_b}"


