import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from contenido.models import Actividad
from login.models import Usuario
from ..model.ModeloAhorcado import AhorcadoJuego
from ..operaciones.OperacionesAhorcado import (
    OperacionesAhorcado,
    actividad_desbloqueada,
)


def _obtener_usuario_perfil(request):
    """
    PRE-1: Obtiene o vincula el modelo Usuario del dominio a partir de request.user.
    """
    if not request.user.is_authenticated:
        return None
    usuario = Usuario.objects.filter(cuenta=request.user).first()
    if not usuario and request.user.email:
        usuario = Usuario.objects.filter(email=request.user.email).first()
    if not usuario:
        nombre = request.user.get_full_name() or request.user.get_username()
        usuario, _ = Usuario.objects.get_or_create(
            cuenta=request.user,
            defaults={'nombre': nombre, 'email': request.user.email or ''}
        )
    return usuario


def _parse_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return {}


class AhorcadoView(View):
    """
    Controlador principal del CU-07: Jugar Ahorcado.
    Maneja la carga del juego, instrucciones y validaciones previas.
    """

    def get(self, request, actividad_id=None):
        """
        # Pasos 1 al 7 del diagrama de secuencia (GET /ahorcado).
        1. Valida autenticación (PRE-1).
        2. Determina actividad_id.
        3. Valida que la actividad sea de ahorcado y esté desbloqueada (PRE-2).
        4. Llama a OperacionesAhorcado.obtenerContenido.
        5. Si contenido es nulo -> Renderiza error (Excepción 1.0.E1).
        6. Renderiza Template.html con instrucciones y botón Comenzar.
        """
        usuario = _obtener_usuario_perfil(request)
        if not usuario:
            return redirect('login')

        if not actividad_id:
            actividad_id = request.GET.get('actividad_id')

        if actividad_id:
            try:
                actividad_id = int(actividad_id)
            except (ValueError, TypeError):
                actividad_id = None

        if not actividad_id:
            actividad_default = Actividad.objects.filter(tipo__iexact='ahorcado').order_by('orden').first()
            if actividad_default:
                actividad_id = actividad_default.id
            else:
                return render(
                    request,
                    'Template.html',
                    {
                        'error': 'No fue posible cargar la actividad',
                        'mensaje_error': 'No existen actividades de tipo ahorcado configuradas.',
                        'url_temario': reverse('mapa_mundos'),
                    }
                )

        actividad = Actividad.objects.select_related('temario__mundo').filter(id=actividad_id).first()
        if not actividad:
            return render(
                request,
                'Template.html',
                {
                    'error': 'No fue posible cargar la actividad',
                    'mensaje_error': 'La actividad solicitada no existe.',
                    'url_temario': reverse('mapa_mundos'),
                }
            )

        if actividad.tipo.lower() != 'ahorcado':
            return redirect('mapa_mundos')

        if not AhorcadoJuego.objects.filter(actividad_id=actividad_id).exists():
            url_temario = '/'
            try:
                if actividad.temario and actividad.temario.mundo_id:
                    url_temario = reverse('temario_mundo', args=[actividad.temario.mundo_id])
                else:
                    url_temario = reverse('mapa_mundos')
            except Exception:
                url_temario = '/'
            return render(
                request,
                'Template.html',
                {
                    'error': 'No fue posible cargar la actividad',
                    'mensaje_error': 'La actividad no cuenta con configuración de Ahorcado.',
                    'url_temario': url_temario,
                }
            )

        if not actividad_desbloqueada(usuario, actividad):
            try:
                if actividad.temario and actividad.temario.mundo_id:
                    return redirect('temario_mundo', mundo_id=actividad.temario.mundo_id)
            except Exception:
                pass
            return redirect('mapa_mundos')

        request.session['ahorcado_actividad_id'] = actividad_id

        ops = OperacionesAhorcado(request)
        contenido = ops.obtenerContenido(usuario, actividad_id)

        if not contenido:
            url_temario = '/'
            try:
                if actividad.temario and actividad.temario.mundo_id:
                    url_temario = reverse('temario_mundo', args=[actividad.temario.mundo_id])
                else:
                    url_temario = reverse('mapa_mundos')
            except Exception:
                url_temario = '/'
            return render(
                request,
                'Template.html',
                {
                    'error': 'No fue posible cargar la actividad',
                    'mensaje_error': 'Ocurrió un problema de base de datos o la actividad no tiene palabras registradas.',
                    'url_temario': url_temario,
                }
            )

        contexto = {
            'actividad': actividad,
            'contenido': contenido,
            'usuario': usuario,
            'url_temario': contenido.get('url_temario', '/'),
        }
        return render(request, 'Template.html', contexto)


@require_POST
def iniciar_partida_view(request):
    """
    # Pasos 8 al 15 del diagrama de secuencia (POST /ahorcado/iniciar).
    """
    usuario = _obtener_usuario_perfil(request)
    if not usuario:
        return JsonResponse({'ok': False, 'mensaje': 'Usuario no autenticado'}, status=401)

    datos = _parse_body(request)
    actividad_id = datos.get('actividad_id') or request.session.get('ahorcado_actividad_id')

    if not actividad_id:
        return JsonResponse({'ok': False, 'mensaje': 'ID de actividad no especificado'}, status=400)

    ops = OperacionesAhorcado(request)
    resultado = ops.iniciarPartida(usuario, int(actividad_id))
    return JsonResponse(resultado)


@require_POST
def validar_letra_view(request):
    """
    # Pasos 16 al 25 del diagrama de secuencia (POST /ahorcado/letra).
    """
    usuario = _obtener_usuario_perfil(request)
    if not usuario:
        return JsonResponse({'ok': False, 'mensaje': 'Usuario no autenticado'}, status=401)

    datos = _parse_body(request)
    letra = datos.get('letra', '')
    ahorcado_id = datos.get('ahorcado_id') or datos.get('actividad_id') or request.session.get('ahorcado_actividad_id')

    if not ahorcado_id:
        return JsonResponse({'ok': False, 'mensaje': 'ID de actividad no especificado'}, status=400)

    if not letra:
        return JsonResponse({'ok': False, 'mensaje': 'No se especificó ninguna letra'}, status=400)

    ops = OperacionesAhorcado(request)
    resultado = ops.validar_letra(usuario, int(ahorcado_id), letra)
    return JsonResponse(resultado)


@require_POST
def solicitar_pista_view(request):
    """
    # Flujos 1.2 y 1.3 del diagrama de secuencia (POST /ahorcado/pista).
    """
    usuario = _obtener_usuario_perfil(request)
    if not usuario:
        return JsonResponse({'ok': False, 'mensaje': 'Usuario no autenticado'}, status=401)

    datos = _parse_body(request)
    ahorcado_id = datos.get('ahorcado_id') or datos.get('actividad_id') or request.session.get('ahorcado_actividad_id')

    if not ahorcado_id:
        return JsonResponse({'ok': False, 'mensaje': 'ID de actividad no especificado'}, status=400)

    ops = OperacionesAhorcado(request)
    resultado = ops.solicitar_pista(usuario, int(ahorcado_id))
    return JsonResponse(resultado)


@require_POST
def abandonar_actividad_view(request):
    """
    # Flujo 1.5 del caso de uso (POST /ahorcado/abandonar).
    """
    usuario = _obtener_usuario_perfil(request)
    if not usuario:
        return JsonResponse({'ok': False, 'mensaje': 'Usuario no autenticado'}, status=401)

    datos = _parse_body(request)
    actividad_id = datos.get('actividad_id') or request.session.get('ahorcado_actividad_id')

    if not actividad_id:
        return JsonResponse({'ok': False, 'mensaje': 'ID de actividad no especificado'}, status=400)

    ops = OperacionesAhorcado(request)
    resultado = ops.abandonar_actividad(usuario, int(actividad_id))
    return JsonResponse(resultado)


@require_POST
def finalizar_ahorcado_view(request):
    """
    # Pasos 22 al 26 del diagrama de secuencia (POST /ahorcado/finalizar).
    """
    usuario = _obtener_usuario_perfil(request)
    if not usuario:
        return JsonResponse({'ok': False, 'mensaje': 'Usuario no autenticado'}, status=401)

    datos = _parse_body(request)
    actividad_id = datos.get('actividad_id') or request.session.get('ahorcado_actividad_id')

    if not actividad_id:
        return JsonResponse({'ok': False, 'mensaje': 'ID de actividad no especificado'}, status=400)

    ops = OperacionesAhorcado(request)
    resultado = ops.finalizar_ahorcado(usuario, int(actividad_id))
    return JsonResponse(resultado)

