from django.urls import path
from . import views

app_name = 'snake'

urlpatterns = [
    path('<int:actividad_id>/', views.vista_snake, name='jugar'),
    path('<int:actividad_id>/finalizar/', views.finalizar_partida, name='finalizar'),
]
