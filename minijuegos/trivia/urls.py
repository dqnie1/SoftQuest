from django.urls import path
from . import views

app_name = 'trivia'
# URLs del minijuego Trivia
urlpatterns = [
	# Abre la trivia general (sin preguntas si no hay id).
	path('trivia/', views.obtener_preguntas, name='trivia'),
	# Abre una trivia específica usando su identificador.
	path('trivia/<int:id_trivia>/', views.obtener_preguntas, name='trivia_detalle'),
	# Valida la respuesta seleccionada por el jugador.
	path('trivia/validar-respuesta/', views.validar_respuesta, name='validar_respuesta'),
	# Guarda el progreso del usuario al terminar la actividad.
	path('trivia/guardar-progreso/', views.guardar_progreso, name='guardar_progreso_trivia'),
]
