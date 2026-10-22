import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SoftQuest.settings')
django.setup()

from contenido.models import Mundo, Temario, Actividad, Insignia
from minijuegos.trivia.models import Trivia, Pregunta, Respuesta
from minijuegos.match.models import MatchJuego, Concepto

def poblar_datos_examen():
    print("Iniciando población de insignias, trivias y conceptos para exámenes...")

    # 1. Asegurar Insignias para cada Mundo (RN-49)
    insignias_datos = {
        1: ("Insignia Explorador de Fundamentos", "Superaste el examen final de Fundamentos de Software", "shield"),
        2: ("Insignia Maestro del Código", "Demostraste tus habilidades en lógica y programación", "terminal"),
        3: ("Insignia Arquitecto de Requerimientos", "Dominaste la clasificación y análisis de requerimientos", "layers"),
    }

    for mundo in Mundo.objects.all():
        nombre, desc, icono = insignias_datos.get(mundo.id, (f"Insignia {mundo.nombre}", f"Completaste {mundo.nombre}", "award"))
        insignia, created = Insignia.objects.get_or_create(
            mundo=mundo,
            defaults={'nombre': nombre, 'descripcion': desc, 'icono': icono}
        )
        if created:
            print(f"Creada insignia para {mundo.nombre}: {insignia.nombre}")
        else:
            print(f"Insignia ya existe para {mundo.nombre}: {insignia.nombre}")

    # 2. Datos para Mundo 2 (Programación Básica)
    try:
        mundo_2 = Mundo.objects.get(id=2)
        temario_2 = Temario.objects.filter(mundo=mundo_2).first()
        if temario_2:
            # Buscar o crear actividad de Trivia para temario 2
            act_trivia_2, _ = Actividad.objects.get_or_create(
                temario=temario_2,
                tipo='trivia',
                defaults={'titulo': 'Banco de Preguntas: Programación', 'orden': 99, 'puntos_max': 0}
            )
            trivia_2, _ = Trivia.objects.get_or_create(actividad=act_trivia_2)

            preguntas_prog = [
                ("¿Qué es una función en programación?", [
                    ("Un bloque de código reutilizable que realiza una tarea específica.", True),
                    ("Una variable que almacena números enteros únicamente.", False),
                    ("Un tipo de bucle infinito que nunca termina.", False),
                    ("Un error de sintaxis que detiene el compilador.", False),
                ]),
                ("¿Qué estructura de control se utiliza para repetir un bloque de código?", [
                    ("Un ciclo o bucle (como for o while).", True),
                    ("Una sentencia if-else.", False),
                    ("Una variable global.", False),
                    ("Un operador aritmético.", False),
                ]),
                ("¿Qué representa un arreglo o lista en memoria?", [
                    ("Una colección secuencial de elementos accesibles mediante índices.", True),
                    ("Una única constante que no puede cambiar de valor.", False),
                    ("Un archivo de texto en el disco duro.", False),
                    ("Una instrucción para apagar la computadora.", False),
                ]),
                ("¿Cuál es el propósito del operador de igualdad (==)?", [
                    ("Comparar si dos valores son iguales.", True),
                    ("Asignar un nuevo valor a una variable.", False),
                    ("Sumar dos números enteros.", False),
                    ("Definir una función nueva.", False),
                ])
            ]

            for p_texto, respuestas in preguntas_prog:
                p, created = Pregunta.objects.get_or_create(trivia=trivia_2, texto=p_texto)
                if created:
                    for r_texto, es_corr in respuestas:
                        Respuesta.objects.create(pregunta=p, texto=r_texto, es_correcta=es_corr)
            print("Preguntas para Mundo 2 creadas/verificadas.")

            # Buscar o crear actividad Match para temario 2
            act_match_2, _ = Actividad.objects.get_or_create(
                temario=temario_2,
                tipo='match_juego',
                defaults={'titulo': 'Conceptos Clave de Programación', 'orden': 100, 'puntos_max': 0}
            )
            match_2, _ = MatchJuego.objects.get_or_create(actividad=act_match_2)
            conceptos_prog = [
                ("Variable", "Contenedor en memoria para almacenar un dato mutable."),
                ("Constante", "Valor que permanece inalterable durante la ejecución."),
                ("Algoritmo", "Conjunto ordenado y finito de pasos para resolver un problema."),
                ("Depuración", "Proceso sistemático de encontrar y corregir errores de software."),
            ]
            for term, defin in conceptos_prog:
                Concepto.objects.get_or_create(match=match_2, termino=term, defaults={'definicion': defin})
            print("Conceptos para Mundo 2 creados/verificados.")
    except Mundo.DoesNotExist:
        pass

    # 3. Datos para Mundo 3 (Ingeniería de Requerimientos)
    try:
        mundo_3 = Mundo.objects.get(id=3)
        temario_3 = Temario.objects.filter(mundo=mundo_3).first()
        if temario_3:
            act_trivia_3, _ = Actividad.objects.get_or_create(
                temario=temario_3,
                tipo='trivia',
                defaults={'titulo': 'Banco de Preguntas: Requerimientos', 'orden': 99, 'puntos_max': 0}
            )
            trivia_3, _ = Trivia.objects.get_or_create(actividad=act_trivia_3)

            preguntas_req = [
                ("¿Cuál es la diferencia fundamental entre un RF y un RNF?", [
                    ("Los RF describen qué hace el sistema y los RNF cómo se comporta o sus restricciones.", True),
                    ("Los RF son opcionales y los RNF son obligatorios.", False),
                    ("Los RNF se implementan en base de datos y los RF en diseño web.", False),
                    ("No existe diferencia, ambos son sinónimos.", False),
                ]),
                ("¿Qué es una Regla de Negocio (RN)?", [
                    ("Una directriz o política del negocio que rige u orienta la operación del sistema.", True),
                    ("Un requerimiento de hardware para instalar el servidor.", False),
                    ("El costo económico de la licencia del software.", False),
                    ("Un lenguaje de programación comercial.", False),
                ]),
                ("¿Cuál de los siguientes es un ejemplo de Requerimiento No Funcional?", [
                    ("El sistema debe responder en menos de 2 segundos al 95% de las consultas.", True),
                    ("El usuario puede registrar una nueva cuenta con email y contraseña.", False),
                    ("El sistema permite exportar reportes a formato PDF.", False),
                    ("El usuario puede cambiar su foto de perfil.", False),
                ]),
                ("¿Qué característica define un requerimiento verificable?", [
                    ("Aquel que se puede comprobar mediante una prueba objetiva o métrica.", True),
                    ("Aquel que describe ideas abstractas sin números.", False),
                    ("Aquel que nunca cambia durante el ciclo de vida del proyecto.", False),
                    ("Aquel redactado en pseudocódigo técnico.", False),
                ])
            ]

            for p_texto, respuestas in preguntas_req:
                p, created = Pregunta.objects.get_or_create(trivia=trivia_3, texto=p_texto)
                if created:
                    for r_texto, es_corr in respuestas:
                        Respuesta.objects.create(pregunta=p, texto=r_texto, es_correcta=es_corr)
            print("Preguntas para Mundo 3 creadas/verificadas.")

            act_match_3, _ = Actividad.objects.get_or_create(
                temario=temario_3,
                tipo='match_juego',
                defaults={'titulo': 'Conceptos de Requerimientos', 'orden': 100, 'puntos_max': 0}
            )
            match_3, _ = MatchJuego.objects.get_or_create(actividad=act_match_3)
            conceptos_req = [
                ("Requerimiento Funcional", "Comportamiento o función que el sistema debe ejecutar ante entradas."),
                ("Requerimiento No Funcional", "Criterio de calidad, rendimiento, seguridad o restricción técnica."),
                ("Regla de Negocio", "Política o condición empresarial impuesta al dominio del problema."),
                ("Ambigüedad", "Defecto de redacción que permite múltiples interpretaciones opuestas."),
            ]
            for term, defin in conceptos_req:
                Concepto.objects.get_or_create(match=match_3, termino=term, defaults={'definicion': defin})
            print("Conceptos para Mundo 3 creados/verificados.")
    except Mundo.DoesNotExist:
        pass

    print("Población completada con éxito.")

if __name__ == '__main__':
    poblar_datos_examen()
