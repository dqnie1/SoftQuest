from django.urls import path
from . import views

app_name = "nave"

urlpatterns = [
    path("<int:actividad_id>/", views.vista_nave, name="jugar"),
    path("<int:actividad_id>/iniciar/", views.iniciar_partida, name="iniciar"),
    path("<int:actividad_id>/clasificar/", views.clasificar_requerimiento, name="clasificar"),
    path("<int:actividad_id>/metrica/", views.validar_metrica, name="metrica"),
    path("<int:actividad_id>/penalizar/", views.penalizar_escudo, name="penalizar"),
    path("<int:actividad_id>/finalizar/", views.finalizar_partida, name="finalizar"),
]
