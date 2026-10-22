from django.urls import path
from . import views

app_name = 'examen'

urlpatterns = [
    path('mundo/<int:mundo_id>/', views.examen_inicio, name='examen_inicio'),
    path('mundo/<int:mundo_id>/presentar/', views.examen_presentar, name='examen_presentar'),
    path('mundo/<int:mundo_id>/calificar/', views.examen_calificar, name='examen_calificar'),
    path('resultado/<int:intento_id>/', views.examen_resultado, name='examen_resultado'),
]
