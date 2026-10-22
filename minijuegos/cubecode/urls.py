from django.urls import path

from . import views

app_name = 'cubecode'

urlpatterns = [
    path('<int:actividad_id>/', views.jugar, name='jugar'),
    path('<int:actividad_id>/comprobar/', views.comprobar, name='comprobar'),
    path('<int:actividad_id>/salir/', views.salir, name='salir'),
    path('<int:actividad_id>/salida/', views.salida, name='salida'),
]
