from django.contrib import admin

from .models import BloqueCubeCode, CubeCode, EjercicioCubeCode, NivelCubeCode, ProgresoCubeCode


class BloqueInline(admin.TabularInline):
    model = BloqueCubeCode
    extra = 0


class EjercicioInline(admin.TabularInline):
    model = EjercicioCubeCode
    extra = 0
    show_change_link = True


@admin.register(CubeCode)
class CubeCodeAdmin(admin.ModelAdmin):
    list_display = ('actividad',)


@admin.register(NivelCubeCode)
class NivelCubeCodeAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'cubecode')
    inlines = [EjercicioInline]


@admin.register(EjercicioCubeCode)
class EjercicioCubeCodeAdmin(admin.ModelAdmin):
    list_display = ('numero', 'titulo', 'nivel')
    inlines = [BloqueInline]


@admin.register(ProgresoCubeCode)
class ProgresoCubeCodeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cubecode', 'puntaje', 'intentos')
