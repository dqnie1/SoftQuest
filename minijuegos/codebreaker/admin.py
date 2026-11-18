from django.contrib import admin
from .models import CodeBreaker, ConceptoCodeBreaker


class ConceptoCodeBreakerInline(admin.TabularInline):
    model = ConceptoCodeBreaker
    extra = 0


@admin.register(CodeBreaker)
class CodeBreakerAdmin(admin.ModelAdmin):
    list_display = ('actividad', 'filas', 'columnas', 'bloques_totales', 'bloques_especiales')
    inlines = [ConceptoCodeBreakerInline]


@admin.register(ConceptoCodeBreaker)
class ConceptoCodeBreakerAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codebreaker', 'tipo', 'efecto_clave', 'nombre_corto')
    list_filter = ('tipo', 'efecto_clave')
    search_fields = ('nombre', 'definicion', 'explicacion')
