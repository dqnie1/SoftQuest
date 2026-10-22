from django.contrib import admin
from .models import IntentoExamen


@admin.register(IntentoExamen)
class IntentoExamenAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'mundo', 'calificacion', 'aprobado', 'tiempo_empleado_segundos', 'fecha_creacion')
    list_filter = ('aprobado', 'mundo', 'fecha_creacion')
    search_fields = ('usuario__nombre', 'usuario__email', 'mundo__nombre')
    readonly_fields = ('fecha_creacion',)
