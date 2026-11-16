from django.urls import path
from . import views

app_name = 'codebreaker'

urlpatterns = [
    path('<int:actividad_id>/', views.vista_codebreaker, name='jugar'),
    path('<int:actividad_id>/finalizar/', views.finalizar_partida, name='finalizar'),
    path('<int:actividad_id>/datos/', views.datos_partida, name='datos'),
]
