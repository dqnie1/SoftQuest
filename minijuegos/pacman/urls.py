from django.urls import path
 
from . import views
 
app_name = "pacman"
 
# En el urls.py del proyecto:  path("pacman/", include("pacman.urls"))
urlpatterns = [
    path("<int:actividad_id>/", views.vista_pacman, name="jugar"),                  # GET  /pacman/<id>/
    path("<int:actividad_id>/iniciar/", views.iniciar_nivel, name="iniciar"),       # POST
    path("<int:actividad_id>/recoger/", views.recoger_linea, name="recoger"),       # POST
    path("<int:actividad_id>/bug/", views.bug_alcanzo, name="bug"),                 # POST
    path("<int:actividad_id>/zona/", views.zona_nueva, name="zona"),                # POST
    path("<int:actividad_id>/finalizar/", views.finalizar_nivel, name="finalizar"), # POST
]