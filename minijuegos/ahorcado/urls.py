from django.urls import path, re_path
from .view.AhorcadoView import (
    AhorcadoView,
    iniciar_partida_view,
    validar_letra_view,
    solicitar_pista_view,
    abandonar_actividad_view,
    finalizar_ahorcado_view,
)

app_name = 'ahorcado'

urlpatterns = [
    # GET /ahorcado y GET /ahorcado/<actividad_id>/
    path('', AhorcadoView.as_view(), name='index'),
    path('<int:actividad_id>/', AhorcadoView.as_view(), name='detalle'),

    # POST /ahorcado/iniciar
    re_path(r'^iniciar/?$', iniciar_partida_view, name='iniciar'),

    # POST /ahorcado/letra
    re_path(r'^letra/?$', validar_letra_view, name='letra'),

    # POST /ahorcado/pista
    re_path(r'^pista/?$', solicitar_pista_view, name='pista'),

    # POST /ahorcado/abandonar
    re_path(r'^abandonar/?$', abandonar_actividad_view, name='abandonar'),

    # POST /ahorcado/finalizar
    re_path(r'^finalizar/?$', finalizar_ahorcado_view, name='finalizar'),
]

