from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import redirect, render

from .models import Usuario
from .forms import LoginForm, RegistroForm


class IniciarSesionView(LoginView):
    authentication_form = LoginForm
    template_name = 'login.html'
    redirect_authenticated_user = True


def registro(request):
    if request.user.is_authenticated:
        return redirect('mapa_mundos')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                Usuario.objects.create(
                    cuenta=user,
                    nombre=form.cleaned_data['nombre'],
                    email=user.email,
                )
            auth_login(request, user)
            return redirect('mapa_mundos')
    else:
        form = RegistroForm()

    return render(request, 'registro.html', {'form': form})


@login_required
def home(request):
    return redirect('mapa_mundos')
