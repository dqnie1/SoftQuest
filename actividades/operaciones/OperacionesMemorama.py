import random


class OperacionesMemorama:
    # revolver pares con metodo shuffle de random
    def revolverPares(self, pares):
        pares_revueltos = list(pares)
        random.shuffle(pares_revueltos) # revulve lo elementos de la lista
        return pares_revueltos

    # se valida por id, ya que las dos cartas deben pertenecer al mismo par
    def validarPar(self, primera_carta_id, segunda_carta_id):
        return primera_carta_id == segunda_carta_id
