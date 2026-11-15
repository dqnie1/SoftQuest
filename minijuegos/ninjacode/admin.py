from django.contrib import admin

from .models import NinjaCode, RequisitoNinja


class RequisitoInline(admin.TabularInline):
    model = RequisitoNinja
    extra = 0


@admin.register(NinjaCode)
class NinjaCodeAdmin(admin.ModelAdmin):
    list_display = ('actividad',)
    inlines = [RequisitoInline]


@admin.register(RequisitoNinja)
class RequisitoNinjaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'texto', 'ninjacode')
    list_filter = ('tipo',)
