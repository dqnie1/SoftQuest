from django.contrib import admin
from .models import Crucigrama, PalabraCrucigrama


class PalabraCrucigramaInline(admin.TabularInline):
    model = PalabraCrucigrama
    extra = 1


class CrucigramaAdmin(admin.ModelAdmin):
    list_display = ("actividad", "filas", "columnas", "tiempo_limite_seg")
    inlines = [PalabraCrucigramaInline]


class PalabraCrucigramaAdmin(admin.ModelAdmin):
    list_display = ("id", "crucigrama", "numero", "direccion", "respuesta", "fila_inicio", "columna_inicio")
    list_filter = ("direccion",)


admin.site.register(Crucigrama, CrucigramaAdmin)
admin.site.register(PalabraCrucigrama, PalabraCrucigramaAdmin)
