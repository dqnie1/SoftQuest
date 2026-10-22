from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import Http404
from .models import Mundo, Temario, Actividad, ProgresoUsuario, ProgresoActividad
from .operaciones.OperacionesContenido import OperacionesContenido

@login_required
def mapa_mundos(request):
    usuario = OperacionesContenido().obtener_usuario(request)
    ops = OperacionesContenido()
    progreso_usuario = ops.actualizar_progreso_mundo(usuario)
    if not progreso_usuario:
        progreso_usuario, _ = ProgresoUsuario.objects.get_or_create(
            usuario=usuario, 
            defaults={'mundo_actual': Mundo.objects.order_by('orden').first()}
        )
    
    mundos = Mundo.objects.all().order_by('orden')
    
    # Calculate stats for sidebar and world states
    mundos_completados = 0
    total_mundos = mundos.count()
    
    for mundo in mundos:
        actividades = Actividad.objects.filter(temario__mundo=mundo)
        total_act = actividades.count()
        act_completadas = ProgresoActividad.objects.filter(
            usuario=usuario,
            actividad__in=actividades,
            estado='completado'
        ).count()
        
        es_completado = (total_act > 0 and act_completadas == total_act)
        
        if es_completado:
            mundo.estado = 'completado'
            mundos_completados += 1
        elif progreso_usuario.mundo_actual and mundo.id == progreso_usuario.mundo_actual.id:
            mundo.estado = 'en_curso'
        elif progreso_usuario.mundo_actual and mundo.orden < progreso_usuario.mundo_actual.orden:
            mundo.estado = 'completado'
            mundos_completados += 1
        else:
            # Temporal para la presentación: el mundo se puede abrir aunque el anterior no esté completo.
            mundo.estado = 'en_curso'

    from contenido.models import InsigniaUsuario
    insignias_count = InsigniaUsuario.objects.filter(usuario=usuario).count()

    context = {
        'mundos': mundos,
        'usuario': usuario,
        'progreso_usuario': progreso_usuario,
        'mundos_completados': mundos_completados,
        'total_mundos': total_mundos,
        'insignias_count': insignias_count,
        'score': sum([p.puntaje for p in ProgresoActividad.objects.filter(usuario=usuario)])
    }
    return render(request, 'mapa_mundos.html', context)

@login_required
def temario_mundo(request, mundo_id):
    usuario = OperacionesContenido().obtener_usuario(request)
    mundo = get_object_or_404(Mundo, id=mundo_id)
    request.session['mundo_id'] = mundo.id
    
    ops = OperacionesContenido()
    progreso_usuario = ops.actualizar_progreso_mundo(usuario)
    if not progreso_usuario:
        progreso_usuario, _ = ProgresoUsuario.objects.get_or_create(
            usuario=usuario, 
            defaults={'mundo_actual': mundo}
        )
    
    # Get all activities ordered by temario order and activity order
    temarios = Temario.objects.filter(mundo=mundo).order_by('orden')
    actividades = list(Actividad.objects.filter(temario__in=temarios).order_by('temario__orden', 'orden'))
    
    total_actividades = len(actividades)
    actividades_completadas = 0
    xp_acumulado = 0
    xp_maximo = sum([act.puntos_max or 0 for act in actividades])
    
    # Check progress for activities
    for idx, act in enumerate(actividades):
        progreso = ProgresoActividad.objects.filter(usuario=usuario, actividad=act).first()
        if progreso and progreso.estado == 'completado':
            act.estado = 'completado'
            act.puntaje_obtenido = progreso.puntaje or 0
            xp_acumulado += progreso.puntaje or 0
            actividades_completadas += 1
        else:
            act.puntaje_obtenido = 0
            # Simple unlock logic: first activity is unlocked, others unlock if previous is completed
            if idx == 0 or (idx > 0 and actividades[idx-1].estado == 'completado'):
                act.estado = 'desbloqueado'
            else:
                act.estado = 'bloqueado'
        
        tipo_normalizado = (act.tipo or '').strip().lower()
        if tipo_normalizado == 'memorama':
            try:
                act.url = reverse('memorama_detalle', kwargs={'id_memorama': act.id})
            except Exception:
                act.url = f'/memorama/{act.id}/'
            act.tipo_display = 'Memorama'
        elif tipo_normalizado == 'trivia':
            try:
                act.url = reverse('trivia:trivia_detalle', kwargs={'id_trivia': act.id})
            except Exception:
                act.url = f'/trivia/{act.id}/'
            act.tipo_display = 'Trivia'
        elif tipo_normalizado in ('match_juego', 'match'):
            try:
                act.url = reverse('match:match_detalle', kwargs={'id_match': act.id})
            except Exception:
                act.url = f'/match/{act.id}/'
            act.tipo_display = 'Match'
        elif tipo_normalizado == 'pacman':
            try:
                act.url = reverse('pacman:jugar', kwargs={'actividad_id': act.id})
            except Exception:
                act.url = f'/pacman/{act.id}/'
            act.tipo_display = 'Pacman'
        elif tipo_normalizado in ('nave', 'nave_espacial'):
            try:
                act.url = reverse('nave:jugar', kwargs={'actividad_id': act.id})
            except Exception:
                act.url = f'/nave/{act.id}/'
            act.tipo_display = 'Nave Espacial'
        elif tipo_normalizado == 'snake':
            try:
                act.url = reverse('snake:jugar', kwargs={'actividad_id': act.id})
            except Exception:
                act.url = f'/snake/{act.id}/'
            act.tipo_display = 'Snake'
        elif tipo_normalizado in ('cubecode', 'cube_code'):
            try:
                act.url = reverse('cubecode:jugar', kwargs={'actividad_id': act.id})
            except Exception:
                act.url = f'/cubecode/{act.id}/'
            act.tipo_display = 'CubeCode'
        else:
            act.url = ''
            act.tipo_display = act.tipo or 'Actividad'
    
    # Filtrar solo actividades públicas regulares
    actividades_visibles = [act for act in actividades if (act.orden or 0) < 90]
    total_visibles = len(actividades_visibles)
    visibles_completadas = sum(1 for act in actividades_visibles if act.estado == 'completado')
    actividades_bloqueadas = sum(1 for act in actividades_visibles if act.estado == 'bloqueado')
    
    # RN-39: El examen se habilita si todas las actividades evaluables del mundo están completadas
    examen_habilitado = (total_visibles > 0 and visibles_completadas == total_visibles)
    
    from minijuegos.examen.models import IntentoExamen
    from contenido.models import InsigniaUsuario
    
    ultimo_intento_examen = IntentoExamen.objects.filter(usuario=usuario, mundo=mundo).order_by('-fecha_creacion').first()
    examen_aprobado = IntentoExamen.objects.filter(usuario=usuario, mundo=mundo, aprobado=True).exists()
    insignias_count = InsigniaUsuario.objects.filter(usuario=usuario).count()
    
    context = {
        'mundo': mundo,
        'actividades': actividades_visibles,
        'xp_maximo': xp_maximo,
        'xp_acumulado': xp_acumulado,
        'total_actividades': total_visibles,
        'actividades_completadas': visibles_completadas,
        'actividades_bloqueadas': actividades_bloqueadas,
        'examen_habilitado': examen_habilitado,
        'examen_aprobado': examen_aprobado,
        'ultimo_intento_examen': ultimo_intento_examen,
        'url_examen': reverse('examen:examen_inicio', kwargs={'mundo_id': mundo.id}),
        'insignias_count': insignias_count,
        'usuario': usuario,
        'score': sum([p.puntaje for p in ProgresoActividad.objects.filter(usuario=usuario)])
    }
    
    return render(request, 'temario_mundo.html', context)
