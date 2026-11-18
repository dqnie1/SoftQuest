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
    path('cubecode/', include('minijuegos.cubecode.urls')),
    path('ninjacode/', include('minijuegos.ninjacode.urls')),
    path('examen/', include('minijuegos.examen.urls')), # url de examen CU-04
    path('ahorcado/', include('minijuegos.ahorcado.urls')), # url de ahorcado CU-07
    path('crucigrama/', include('minijuegos.crucigrama.urls')), # url de crucigrama CU-09
    path('codebreaker/', include('minijuegos.codebreaker.urls')), # url de codebreaker CU-11
    path('sopaletras/', include('minijuegos.sopaletras.urls')), # url de sopa de letras CU-12
]

# Servir archivos estaticos durante el desarrollo.
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)