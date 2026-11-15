from django.db import models

from contenido.models import Actividad


class TipoRequisitoNinja(models.TextChoices):
    FUNCIONAL = 'FUNCIONAL', 'Funcional'
    NO_FUNCIONAL = 'NO_FUNCIONAL', 'No funcional'


class NinjaCode(models.Model):
    actividad = models.OneToOneField(
        Actividad,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='ninjacode',
    )

    class Meta:
        db_table = 'ninjacode'

    def __str__(self):
        return f'NinjaCode: {self.actividad}'


class RequisitoNinja(models.Model):
    id = models.AutoField(primary_key=True)
    ninjacode = models.ForeignKey(
        NinjaCode,
        on_delete=models.CASCADE,
        related_name='requisitos',
    )
    texto = models.CharField(max_length=500)
    tipo = models.CharField(max_length=20, choices=TipoRequisitoNinja.choices)

    class Meta:
        db_table = 'requisito_ninja'

    def __str__(self):
        return f'[{self.tipo}] {self.texto[:60]}'
