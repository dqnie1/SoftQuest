from django.contrib import admin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'cuenta')
    search_fields = ('nombre', 'email', 'cuenta__username')
