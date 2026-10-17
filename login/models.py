from django.db import models
from django.conf import settings


class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    cuenta = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_contenido',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return self.nombre
