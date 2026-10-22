"""Ejercicios de CubeCode. Los usan las migraciones de siembra."""

NIVELES = [
    {
        'numero': 1,
        'nombre': 'Fundamentos',
        'ejercicios': [
            {
                'numero': 1,
                'titulo': 'Precio con descuento',
                'objetivo': 'A un precio de 250 pesos réstale un descuento de 50 y muestra el total.',
                'bloques': [
                    {'texto': 'precio = 250', 'orden': 1, 'pista': 'Guardar el precio'},
                    {'texto': 'descuento = 50', 'orden': 2, 'pista': 'Guardar el descuento'},
                    {'texto': 'total = precio - descuento', 'orden': 3, 'pista': 'Restar el descuento'},
                    {'texto': 'print(total)', 'orden': 4, 'pista': 'Mostrar el total'},
                    {'texto': 'total = precio + descuento', 'orden': None, 'pista': ''},
                    {'texto': 'print(precio)', 'orden': None, 'pista': ''},
                ],
            },
            {
                'numero': 2,
                'titulo': 'Promedio de dos calificaciones',
                'objetivo': 'Calcular el promedio de dos calificaciones y mostrar el resultado.',
                'bloques': [
                    {'texto': 'calificacion1 = 8', 'orden': 1, 'pista': 'Guardar la primera calificación'},
                    {'texto': 'calificacion2 = 6', 'orden': 2, 'pista': 'Guardar la segunda calificación'},
                    {'texto': 'promedio = (calificacion1 + calificacion2) / 2', 'orden': 3, 'pista': 'Calcular el promedio'},
                    {'texto': 'print(promedio)', 'orden': 4, 'pista': 'Mostrar el promedio'},
                    {'texto': 'promedio = calificacion1 + calificacion2', 'orden': None, 'pista': ''},
                    {'texto': 'print(calificacion1)', 'orden': None, 'pista': ''},
                ],
            },
            {
                'numero': 3,
                'titulo': 'El doble de un número',
                'objetivo': 'Calcular el doble de 7 y mostrarlo.',
                'bloques': [
                    {'texto': 'numero = 7', 'orden': 1, 'pista': 'Guardar el número'},
                    {'texto': 'doble = numero * 2', 'orden': 2, 'pista': 'Multiplicar por dos'},
                    {'texto': 'print(doble)', 'orden': 3, 'pista': 'Mostrar el doble'},
                    {'texto': 'doble = numero + 2', 'orden': None, 'pista': ''},
                    {'texto': 'print(numero)', 'orden': None, 'pista': ''},
                ],
            },
        ],
    },
    {
        'numero': 2,
        'nombre': 'Lógica condicional',
        'ejercicios': [
            {
                'numero': 1,
                'titulo': '¿Aprobó?',
                'objetivo': 'Si la calificación es 6 o más, mostrar "Aprobado". Si no, mostrar "Reprobado".',
                'bloques': [
                    {'texto': 'calificacion = 8', 'orden': 1, 'pista': 'Guardar la calificación'},
                    {'texto': 'if calificacion >= 6:', 'orden': 2, 'pista': 'Preguntar si aprueba'},
                    {'texto': 'print("Aprobado")', 'orden': 3, 'pista': 'Mensaje de aprobado'},
                    {'texto': 'else:', 'orden': 4, 'pista': 'El caso contrario'},
                    {'texto': 'print("Reprobado")', 'orden': 5, 'pista': 'Mensaje de reprobado'},
                    {'texto': 'if calificacion > 10:', 'orden': None, 'pista': ''},
                    {'texto': 'print("Excelente")', 'orden': None, 'pista': ''},
                ],
            },
            {
                'numero': 2,
                'titulo': 'Temperatura',
                'objetivo': 'Si la temperatura pasa de 37, mostrar "Alta". Si no, mostrar "Normal".',
                'bloques': [
                    {'texto': 'temperatura = 38', 'orden': 1, 'pista': 'Guardar la temperatura'},
                    {'texto': 'if temperatura > 37:', 'orden': 2, 'pista': 'Preguntar si está alta'},
                    {'texto': 'print("Alta")', 'orden': 3, 'pista': 'Mensaje de temperatura alta'},
                    {'texto': 'else:', 'orden': 4, 'pista': 'El caso contrario'},
                    {'texto': 'print("Normal")', 'orden': 5, 'pista': 'Mensaje de temperatura normal'},
                    {'texto': 'if temperatura < 37:', 'orden': None, 'pista': ''},
                    {'texto': 'print("Fiebre")', 'orden': None, 'pista': ''},
                ],
            },
            {
                'numero': 3,
                'titulo': 'El mayor de dos números',
                'objetivo': 'Mostrar el mayor entre x y y.',
                'bloques': [
                    {'texto': 'x = 4', 'orden': 1, 'pista': 'Guardar x'},
                    {'texto': 'y = 9', 'orden': 2, 'pista': 'Guardar y'},
                    {'texto': 'if y > x:', 'orden': 3, 'pista': 'Preguntar si y es mayor'},
                    {'texto': 'print(y)', 'orden': 4, 'pista': 'Mostrar y'},
                    {'texto': 'else:', 'orden': 5, 'pista': 'El caso contrario'},
                    {'texto': 'print(x)', 'orden': 6, 'pista': 'Mostrar x'},
                    {'texto': 'if y < x:', 'orden': None, 'pista': ''},
                    {'texto': 'print(x + y)', 'orden': None, 'pista': ''},
                ],
            },
        ],
    },
    {
        'numero': 3,
        'nombre': 'Bucles',
        'ejercicios': [
            {
                'numero': 1,
                'titulo': 'Sumar una lista',
                'objetivo': 'Sumar 1, 2 y 3 con un ciclo for y mostrar el total.',
                'bloques': [
                    {'texto': 'numeros = [1, 2, 3]', 'orden': 1, 'pista': 'Crear la lista'},
                    {'texto': 'suma = 0', 'orden': 2, 'pista': 'Empezar la suma en cero'},
                    {'texto': 'for numero in numeros:', 'orden': 3, 'pista': 'Recorrer cada número'},
                    {'texto': 'suma = suma + numero', 'orden': 4, 'pista': 'Acumular el número'},
                    {'texto': 'print(suma)', 'orden': 5, 'pista': 'Mostrar la suma'},
                    {'texto': 'suma = numero', 'orden': None, 'pista': ''},
                    {'texto': 'print(numeros)', 'orden': None, 'pista': ''},
                ],
            },
            {
                'numero': 2,
                'titulo': 'Contar elementos',
                'objetivo': 'Contar cuántas palabras hay en la lista y mostrar ese número.',
                'bloques': [
                    {'texto': 'frutas = ["pera", "uva"]', 'orden': 1, 'pista': 'Crear la lista'},
                    {'texto': 'total = 0', 'orden': 2, 'pista': 'Empezar el contador en cero'},
                    {'texto': 'for fruta in frutas:', 'orden': 3, 'pista': 'Recorrer cada palabra'},
                    {'texto': 'total = total + 1', 'orden': 4, 'pista': 'Contar uno más'},
                    {'texto': 'print(total)', 'orden': 5, 'pista': 'Mostrar el total'},
                    {'texto': 'total = 1', 'orden': None, 'pista': ''},
                    {'texto': 'print(frutas)', 'orden': None, 'pista': ''},
                ],
            },
            {
                'numero': 3,
                'titulo': 'Letras de una palabra',
                'objetivo': 'Mostrar, en orden, cada letra de la palabra "sol".',
                'bloques': [
                    {'texto': 'palabra = "sol"', 'orden': 1, 'pista': 'Guardar la palabra'},
                    {'texto': 'print(palabra[0])', 'orden': 2, 'pista': 'Mostrar la primera letra'},
                    {'texto': 'print(palabra[1])', 'orden': 3, 'pista': 'Mostrar la segunda letra'},
                    {'texto': 'print(palabra[2])', 'orden': 4, 'pista': 'Mostrar la tercera letra'},
                    {'texto': 'print(palabra[3])', 'orden': None, 'pista': ''},
                    {'texto': 'print(palabra)', 'orden': None, 'pista': ''},
                ],
            },
        ],
    },
]
