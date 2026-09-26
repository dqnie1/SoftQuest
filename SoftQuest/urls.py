from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('mapa_mundos')),
    path('', include('contenido.urls')),
    path('', include('minijuegos.memorama.urls')),
    path('', include('minijuegos.trivia.urls')),
    path('', include('minijuegos.match.urls')), #url de minijuego
]

# Servir archivos estaticos durante el desarrollo.
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)