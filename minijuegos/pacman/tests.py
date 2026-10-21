from django.test import SimpleTestCase

from .operaciones.OperacionesPacman import OperacionesPacman


class PuntuacionPacmanTests(SimpleTestCase):
    def setUp(self):
        self.estado = {
            "lineas": [
                {"id": 1, "codigo": "linea 1", "puntos": 100},
                {"id": 2, "codigo": "linea 2", "puntos": 150},
            ],
            "recogidas": [],
            "puntaje": 500,
            "base": 500,
            "titulo": "Reto",
            "salida": "ok",
            "vidas": 3,
            "bugs": 0,
        }

    def test_el_puntaje_maximo_es_la_suma_de_las_partes_recogidas(self):
        OperacionesPacman.registrar_fragmento(self.estado)
        OperacionesPacman.registrar_fragmento(self.estado)

        resumen = OperacionesPacman.calcular_resumen_nivel(self.estado)

        self.assertEqual(resumen["puntos_nivel"], 250)
        self.assertEqual(resumen["puntaje_total"], 750)
        self.assertNotIn("bonus", resumen)

    def test_al_devolver_una_parte_se_restan_sus_puntos(self):
        OperacionesPacman.registrar_fragmento(self.estado)

        devuelta = OperacionesPacman.devolver_fragmento_al_tablero(self.estado)

        self.assertEqual(devuelta, 1)
        self.assertEqual(self.estado["puntaje"], self.estado["base"])
