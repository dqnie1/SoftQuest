from django.db import models
from login.models import Usuario

# Create your models here.
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
# Progreso
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Insignias de Mundos (RN-49)
# ---------------------------------------------------------------------------

class Insignia(models.Model):
    id = models.AutoField(primary_key=True)
    mundo = models.OneToOneField(
        Mundo, on_delete=models.CASCADE, related_name="insignia"
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True)
    icono = models.CharField(max_length=50, default="award")

    class Meta:
        db_table = "insignia"

    def __str__(self):
        return f"Insignia: {self.nombre} ({self.mundo.nombre})"


class InsigniaUsuario(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="insignias_obtenidas"
    )
    insignia = models.ForeignKey(
        Insignia, on_delete=models.CASCADE, related_name="usuarios_ganadores"
    )
    fecha_obtencion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "insignia_usuario"
        unique_together = ('usuario', 'insignia')

    def __str__(self):
        return f"{self.usuario.nombre} - {self.insignia.nombre}"