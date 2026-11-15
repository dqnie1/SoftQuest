from django.urls import path
from . import views

app_name = 'crucigrama'

urlpatterns = [
    path('<int:actividad_id>/', views.vista_crucigrama, name='jugar'),
    path('<int:actividad_id>/finalizar/', views.finalizar_partida, name='finalizar'),
]
