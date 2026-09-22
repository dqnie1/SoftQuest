# actividades/operaciones/OperacionesMatch.py
import random

from ..models import Concepto


class OperacionesMatch:
    """
    Lógica de negocio del minijuego Match. Es la única clase que consulta
    directamente a Concepto/DaoConcepto; ViewMatch nunca le habla al
    modelo de conceptos directamente.
    """

    def obtenerListaConceptosSinProcesar(self, id_match):
        """
        Corresponde al paso 4 del diagrama de secuencia: obtiene, tal cual
        están guardados, todos los conceptos de un match.
        """
        return list(Concepto.objects.filter(match_id=id_match))

    def obtenerTerminosYDefinicionesRevuelta(self, id_match):
        """
        Corresponde a los pasos 3-8: arma la lista de conceptos que se le
        muestra al jugador, con el orden revuelto para que no delate la
        posición correcta.
        """
        conceptos = self.obtenerListaConceptosSinProcesar(id_match)
        random.shuffle(conceptos)
        return conceptos

    def obtenerListaConceptosCorrecta(self, id_match):
        """
        Corresponde a los pasos 15-16: regresa el emparejamiento correcto
        (término_id, definición_id) para que ViewMatch compare contra el
        intento del jugador. Como término y definición viven en la misma
        fila de Concepto, el emparejamiento correcto es termino_id == id
        de su propia fila.
        """
        conceptos = self.obtenerListaConceptosSinProcesar(id_match)
        return [
            {'termino_id': c.id, 'definicion_id': c.id}
            for c in conceptos
        ]