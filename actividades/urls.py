from django.urls import path
from . import views

# aqui van las URLS de toda la app de actividades
urlpatterns = [
	# Abre el memorama general con todos los pares disponibles.
	path('memorama/', views.obetenerPares, name='memorama'),
	# Abre un memorama específico usando su identificador.
	path('memorama/<int:id_memorama>/', views.obetenerPares, name='memorama_detalle'),
	# Comprueba si las dos cartas seleccionadas forman un par.
	path('memorama/validar-par/', views.validar_par, name='validar_par'),
	# Guarda el progreso del usuario al completar la actividad.
	path('memorama/guardar-progreso/', views.guardar_progreso, name='guardar_progreso'),
]
