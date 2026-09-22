from django.urls import path
from . import views

# aquí van las URLs de toda la app de actividades
urlpatterns = [
    # Abre el Match general con todos los conceptos disponibles.
    path('match/', views.obtenerConceptos, name='match'),

    # Abre un Match específico usando su identificador.
    path('match/<int:id_match>/', views.obtenerConceptos, name='match_detalle'),

    # Comprueba si las dos cartas seleccionadas forman un Match.
    path('match/validar-match/', views.validar_match, name='validar_match'),

    # Guarda el progreso del usuario al completar la actividad.
    path('match/guardar-progreso/', views.guardar_progreso, name='guardar_progreso'),
]