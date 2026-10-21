from django.core.exceptions import ValidationError
from django.db import models

from contenido.models import Actividad


class TipoRequerimiento(models.TextChoices):
    RF = 'RF', 'Requerimiento Funcional'
    RNF = 'RNF', 'Requerimiento No Funcional'
    RN = 'RN', 'Regla de Negocio'


class NaveEspacial(models.Model):
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='nave_espacial',
    )

    class Meta:
        db_table = 'nave_espacial'
        verbose_name = 'Nave Espacial'
        verbose_name_plural = 'Naves Espaciales'

    def __str__(self):
        return f"Nave Espacial: {self.actividad.titulo if self.actividad else self.pk}"


class Requerimiento(models.Model):
    id = models.AutoField(primary_key=True)
    nave_espacial = models.ForeignKey(
        NaveEspacial,
        on_delete=models.CASCADE,
        related_name='requerimientos',
    )
    texto = models.CharField(max_length=500)
    tipo = models.CharField(max_length=10, choices=TipoRequerimiento.choices)
    explicacion = models.TextField()

    class Meta:
        db_table = 'requerimiento'
        verbose_name = 'Requerimiento'
        verbose_name_plural = 'Requerimientos'

    def __str__(self):
        return f"[{self.tipo}] {self.texto[:60]}"


class AnomaliaAmbigua(models.Model):
    id = models.AutoField(primary_key=True)
    nave_espacial = models.ForeignKey(
        NaveEspacial,
        on_delete=models.CASCADE,
        related_name='anomalias',
    )
    texto_ambiguo = models.CharField(max_length=500)
    explicacion = models.TextField()
    tiempo_limite_seg = models.PositiveIntegerField(default=5)

    class Meta:
        db_table = 'anomalia_ambigua'
        verbose_name = 'Anomalía Ambigua'
        verbose_name_plural = 'Anomalías Ambiguas'

    def __str__(self):
        return f"Anomalía: {self.texto_ambiguo[:60]}"

    def clean(self):
        super().clean()
        if self.pk:
            opciones = self.opciones.all()
            if opciones.exists():
                if opciones.count() < 2:
                    raise ValidationError("Cada anomalía debe tener al menos 2 opciones de métrica.")
                correctas = opciones.filter(es_correcta=True).count()
                if correctas != 1:
                    raise ValidationError("Cada anomalía debe tener exactamente una opción correcta.")


class OpcionMetrica(models.Model):
    id = models.AutoField(primary_key=True)
    anomalia = models.ForeignKey(
        AnomaliaAmbigua,
        on_delete=models.CASCADE,
        related_name='opciones',
    )
    texto = models.CharField(max_length=500)
    es_correcta = models.BooleanField(default=False)

    class Meta:
        db_table = 'opcion_metrica'
        verbose_name = 'Opción de Métrica'
        verbose_name_plural = 'Opciones de Métrica'

    def __str__(self):
        estado = "Correcta" if self.es_correcta else "Incorrecta"
        return f"[{estado}] {self.texto[:60]}"
