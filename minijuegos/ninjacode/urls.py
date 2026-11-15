from django.urls import path

from . import views

app_name = 'ninjacode'

urlpatterns = [
    path('<int:actividad_id>/', views.jugar, name='jugar'),
    path('<int:actividad_id>/guardar-progreso/', views.guardar_progreso, name='guardar_progreso'),
]
