from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import Http404
from .models import Mundo, Temario, Actividad, ProgresoUsuario, ProgresoActividad, Usuario

def get_current_user():
    # Helper for the mock user until auth is implemented
    user = Usuario.objects.first()
    return user

def mapa_mundos(request):
    usuario = get_current_user()
    progreso_usuario, _ = ProgresoUsuario.objects.get_or_create(
        usuario=usuario, 
        defaults={'mundo_actual_id': 1} # Default to world 1
    )
    
    mundos = Mundo.objects.all().order_by('orden')
    
    # Calculate stats for sidebar
    mundos_completados = 0
    total_mundos = mundos.count()
    
    for mundo in mundos:
        if mundo.orden < progreso_usuario.mundo_actual.orden:
            mundo.estado = 'completado'
            mundos_completados += 1
        elif mundo.orden == progreso_usuario.mundo_actual.orden:
            mundo.estado = 'en_curso'
        else:
            mundo.estado = 'bloqueado'
            # Prereq logic (just an example for the frontend)
            mundo.prereq = Mundo.objects.filter(orden=mundo.orden-1).first()

    context = {
        'mundos': mundos,
        'usuario': usuario,
        'progreso_usuario': progreso_usuario,
        'mundos_completados': mundos_completados,
        'total_mundos': total_mundos,
        'score': sum([p.puntaje for p in ProgresoActividad.objects.filter(usuario=usuario)])
    }
    return render(request, 'mapa_mundos.html', context)

def temario_mundo(request, mundo_id):
    usuario = get_current_user()
    mundo = get_object_or_404(Mundo, id=mundo_id)
    request.session['mundo_id'] = mundo.id
    
    progreso_usuario, _ = ProgresoUsuario.objects.get_or_create(
        usuario=usuario, 
        defaults={'mundo_actual_id': 1}
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
                act.url = reverse('trivia_detalle', kwargs={'id_trivia': act.id})
            except Exception:
                act.url = f'/trivia/{act.id}/'
            act.tipo_display = 'Trivia'
        elif tipo_normalizado in ('match_juego', 'match'):
            act.url = ''
            act.tipo_display = 'Match'
        else:
            act.url = ''
            act.tipo_display = act.tipo or 'Actividad'
    
    actividades_bloqueadas = sum(1 for act in actividades if act.estado == 'bloqueado')
    
    context = {
        'mundo': mundo,
        'actividades': actividades,
        'xp_maximo': xp_maximo,
        'xp_acumulado': xp_acumulado,
        'total_actividades': total_actividades,
        'actividades_completadas': actividades_completadas,
        'actividades_bloqueadas': actividades_bloqueadas,
        'usuario': usuario,
        'score': sum([p.puntaje for p in ProgresoActividad.objects.filter(usuario=usuario)])
    }
    
    return render(request, 'temario_mundo.html', context)
