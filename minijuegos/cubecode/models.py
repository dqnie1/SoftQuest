from django.db import models

from contenido.models import Actividad
from login.models import Usuario


class CubeCode(models.Model):
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='cubecode',
    )

    class Meta:
        db_table = 'cubecode'

    def __str__(self):
        return f'CubeCode: {self.actividad}'


class NivelCubeCode(models.Model):
    cubecode = models.ForeignKey(
        CubeCode,
        on_delete=models.CASCADE,
        related_name='niveles',
    )
    numero = models.PositiveIntegerField()
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'nivel_cubecode'
        ordering = ['numero']
        constraints = [
            models.UniqueConstraint(
                fields=['cubecode', 'numero'],
                name='nivel_cubecode_unico',
            ),
        ]

    def __str__(self):
        return f'Nivel {self.numero}: {self.nombre}'


class EjercicioCubeCode(models.Model):
    nivel = models.ForeignKey(
        NivelCubeCode,
        on_delete=models.CASCADE,
        related_name='ejercicios',
    )
    numero = models.PositiveIntegerField()
    titulo = models.CharField(max_length=150)
    objetivo = models.TextField()

    class Meta:
        db_table = 'ejercicio_cubecode'
        ordering = ['nivel__numero', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['nivel', 'numero'],
                name='ejercicio_cubecode_unico',
            ),
        ]

    def __str__(self):
        return self.titulo


class BloqueCubeCode(models.Model):
    ejercicio = models.ForeignKey(
        EjercicioCubeCode,
        on_delete=models.CASCADE,
        related_name='bloques',
    )
    texto = models.CharField(max_length=300)
    orden_solucion = models.PositiveIntegerField(null=True, blank=True)
    pista = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        db_table = 'bloque_cubecode'

    def __str__(self):
        return self.texto


class ProgresoCubeCode(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='progresos_cubecode',
    )
    cubecode = models.ForeignKey(
        CubeCode,
        on_delete=models.CASCADE,
        related_name='progresos',
    )
    ejercicios_hechos = models.JSONField(default=list)
    puntaje = models.IntegerField(default=0)
    intentos = models.IntegerField(default=0)

    class Meta:
        db_table = 'progreso_cubecode'
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'cubecode'],
                name='progreso_cubecode_unico',
            ),
        ]

    def __str__(self):
        return f'{self.usuario} · CubeCode {self.puntaje}'
