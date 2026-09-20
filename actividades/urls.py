from django.urls import path
from . import views

# aqui van las URLS de toda la app de actividades
urlpatterns = [
	path('memorama/', views.obetenerPares, name='memorama'),
	path('memorama/<int:id_memorama>/', views.obetenerPares, name='memorama_detalle'),
	path('memorama/validar-par/', views.validar_par, name='validar_par'),
	path('memorama/guardar-progreso/', views.guardar_progreso, name='guardar_progreso'),
]
