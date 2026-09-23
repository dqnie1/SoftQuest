from django.urls import path
from . import views

urlpatterns = [
    path('mundos/', views.mapa_mundos, name='mapa_mundos'),
    path('mundos/<int:mundo_id>/', views.temario_mundo, name='temario_mundo'),
]
