from django.db import models


# ---------------------------------------------------------------------------
# Estructura del contenido: MUNDO -> TEMARIO -> ACTIVIDAD
# ---------------------------------------------------------------------------

class Mundo(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    orden = models.IntegerField()

    class Meta:
        db_table = "mundo"

    def __str__(self):
        return self.nombre


class Temario(models.Model):
    id = models.AutoField(primary_key=True)
    mundo = models.ForeignKey(
        Mundo, on_delete=models.CASCADE, related_name="temarios"
    )  # columna: mundo_id
    nombre = models.CharField(max_length=100)
    orden = models.IntegerField()

    class Meta:
        db_table = "temario"

    def __str__(self):
        return self.nombre


class Actividad(models.Model):
    id = models.AutoField(primary_key=True)
    temario = models.ForeignKey(
        Temario, on_delete=models.CASCADE, related_name="actividades"
    )  # columna: temario_id
    tipo = models.CharField(max_length=30)  # trivia / match_juego / memorama
    titulo = models.CharField(max_length=150)
    orden = models.IntegerField()
    puntos_max = models.IntegerField()

    class Meta:
        db_table = "actividad"

    def __str__(self):
        return self.titulo


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

    @staticmethod
    def todos_los_pares(id_memorama=None):
        if id_memorama is None:
            return [] # regresa una lista nula si no se especifica el id memoama
        return list(Par.objects.filter(memorama_id=id_memorama))

    @property
    def parteA(self):
        return self.elemento_a

    @property
    def parteB(self):
        return self.elemento_b

# ---------------------------------------------------------------------------
# Usuario y progreso
# ---------------------------------------------------------------------------

class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)

    class Meta:
        db_table = "usuario"

    def __str__(self):
        return self.nombre


class ProgresoActividad(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="progresos_actividad"
    )  # columna: usuario_id
    actividad = models.ForeignKey(
        Actividad, on_delete=models.CASCADE, related_name="progresos"
    )  # columna: actividad_id
    estado = models.CharField(max_length=30)
    puntaje = models.IntegerField(default=0)
    intentos = models.IntegerField(default=0)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "progreso_actividad"

    def __str__(self):
        return f"{self.usuario} - {self.actividad} ({self.estado})"


class ProgresoUsuario(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name="progreso"
    )  # columna: usuario_id (relación 1 a 1: "tiene")
    mundo_actual = models.ForeignKey(
        Mundo, on_delete=models.PROTECT, related_name="progresos_usuario"
    )  # columna: mundo_actual_id ("es_mundo_actual_de")
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "progreso_usuario"

    def __str__(self):
        return f"{self.usuario} - {self.mundo_actual}"