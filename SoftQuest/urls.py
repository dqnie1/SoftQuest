from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from django.http import HttpResponse

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('favicon.ico', lambda request: HttpResponse(status=204)),
    path('', include('login.urls')),
    path('', lambda request: redirect('mapa_mundos')),
    path('', include('contenido.urls')),
    path('', include('minijuegos.memorama.urls')),
    path('', include('minijuegos.trivia.urls')),
    path('', include('minijuegos.match.urls')), #url de minijuego
    path('pacman/', include('minijuegos.pacman.urls')), #url de minijuego
    path('nave/', include('minijuegos.nave.urls')), #url de minijuego nave espacial
    path('snake/', include('minijuegos.snake.urls')), #url de minijuego snake
]

# Servir archivos estaticos durante el desarrollo.
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)