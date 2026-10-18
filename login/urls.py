from django.contrib.auth import views as auth_views
from django.urls import path

from .views import IniciarSesionView, registro


urlpatterns = [
    path('login/', IniciarSesionView.as_view(), name='login'),
    path('registro/', registro, name='registro'),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout',
    ),
]
