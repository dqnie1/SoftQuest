from django.contrib import admin
from .models import Snake, NivelSnake, ItemNivel


class ItemNivelInline(admin.TabularInline):
    model = ItemNivel
    extra = 1


class NivelSnakeAdmin(admin.ModelAdmin):
    list_display = ("id", "snake", "numero", "titulo", "tema", "filas", "columnas", "velocidad_ms")
    inlines = [ItemNivelInline]


class SnakeAdmin(admin.ModelAdmin):
    list_display = ("actividad",)


admin.site.register(Snake, SnakeAdmin)
admin.site.register(NivelSnake, NivelSnakeAdmin)
admin.site.register(ItemNivel)
