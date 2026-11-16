from django.contrib import admin
from .models import SopaLetras, PalabraSopa


class PalabraSopaInline(admin.TabularInline):
    model = PalabraSopa
    extra = 0


@admin.register(SopaLetras)
class SopaLetrasAdmin(admin.ModelAdmin):
    list_display = ('actividad', 'dimension', 'total_palabras')
    inlines = [PalabraSopaInline]


@admin.register(PalabraSopa)
class PalabraSopaAdmin(admin.ModelAdmin):
    list_display = ('palabra', 'nombre', 'sopaletras', 'tipo_ejemplo')
    search_fields = ('palabra', 'nombre', 'definicion', 'explicacion')
