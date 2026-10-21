from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
import random

from minijuegos.nave.models import AnomaliaAmbigua, OpcionMetrica, Requerimiento


@dataclass
class EstadoPartida:
    escudo: int = 100
    combo: int = 1
    puntaje: int = 0
    aciertos_rf: int = 0
    aciertos_rnf: int = 0
    aciertos_rn: int = 0
    partida_terminada: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls()
        return cls(
            escudo=int(data.get('escudo', 100)),
            combo=int(data.get('combo', 1)),
            puntaje=int(data.get('puntaje', 0)),
            aciertos_rf=int(data.get('aciertos_rf', 0)),
            aciertos_rnf=int(data.get('aciertos_rnf', 0)),
            aciertos_rn=int(data.get('aciertos_rn', 0)),
            partida_terminada=bool(data.get('partida_terminada', False)),
        )


class OperacionesNave:
    ESCUDO_INICIAL = 100             # RN-37
    PENALIZACION_ESCUDO = 10        # RN-37
    COMBO_INICIAL = 1               # RN-38
    COMBO_MAXIMO = 4                # RN-38
    PUNTOS_BASE_REQUERIMIENTO = 150 # Prototipo
    PUNTOS_ANOMALIA = 500           # Prototipo
    XP_MAXIMO = 100                 # RN-31
    UMBRAL_DESBLOQUEO = 70          # XP
    PUNTAJE_META = 10000

    MOTIVOS_VALIDOS = {"tiempo_agotado", "no_interceptado", "impacto_nave"}

    @classmethod
    def redondeo_half_up(cls, val):
        """Redondeo hacia arriba a la mitad (0.5 -> 1)."""
        d = Decimal(str(val))
        return int(d.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    @classmethod
    def revolverBanco(cls, requerimientos, anomalias):
        """Devuelve ambas listas en orden aleatorio."""
        req_list = list(requerimientos)
        anom_list = list(anomalias)
        random.shuffle(req_list)
        random.shuffle(anom_list)
        return req_list, anom_list

    @classmethod
    def iniciarPartida(cls):
        """Devuelve un EstadoPartida inicial."""
        return EstadoPartida(
            escudo=cls.ESCUDO_INICIAL,
            combo=cls.COMBO_INICIAL,
            puntaje=0,
            aciertos_rf=0,
            aciertos_rnf=0,
            aciertos_rn=0,
            partida_terminada=False,
        )

    @classmethod
    def validarClasificacion(cls, tipo_laser, requerimiento_id, estado, banco_req=None):
        """
        Compara tipo_laser con Requerimiento.tipo.
        Si la partida ya terminó, rechaza el evento.
        Devuelve: correcto (bool), explicacion, tipo_correcto, estado
        """
        if estado.partida_terminada:
            return False, "La partida ya ha finalizado.", "", estado

        req_tipo = None
        req_explicacion = ""

        # Usar banco en memoria si está disponible para evitar latencia de red
        if banco_req and (requerimiento_id in banco_req or str(requerimiento_id) in banco_req):
            info = banco_req.get(requerimiento_id) or banco_req.get(str(requerimiento_id))
            req_tipo = info.get("tipo")
            req_explicacion = info.get("explicacion", "")
        else:
            try:
                req = Requerimiento.objects.get(id=requerimiento_id)
                req_tipo = req.tipo
                req_explicacion = req.explicacion
            except Requerimiento.DoesNotExist:
                return False, "Requerimiento no encontrado.", "", estado

        laser_normalizado = (tipo_laser or '').strip().upper()
        if laser_normalizado == req_tipo:
            # Correcta: puntaje += PUNTOS_BASE * combo actual, luego incrementa combo
            estado.puntaje += cls.PUNTOS_BASE_REQUERIMIENTO * estado.combo
            estado.combo = min(estado.combo + 1, cls.COMBO_MAXIMO)
            if req_tipo == 'RF':
                estado.aciertos_rf += 1
            elif req_tipo == 'RNF':
                estado.aciertos_rnf += 1
            elif req_tipo == 'RN':
                estado.aciertos_rn += 1
            correcto = True
        else:
            # Incorrecta (RN-34): escudo -= PENALIZACION y combo = COMBO_INICIAL
            estado.escudo = max(0, estado.escudo - cls.PENALIZACION_ESCUDO)
            estado.combo = cls.COMBO_INICIAL
            if estado.escudo <= 0:
                estado.escudo = 0
                estado.partida_terminada = True
            correcto = False

        return correcto, req_explicacion, req_tipo, estado

    @classmethod
    def validarMetrica(cls, opcion_id, anomalia_id, estado, banco_anom=None):
        """
        Valida la opción elegida para resolver una anomalía ambigua.
        Si la partida ya terminó, rechaza el evento.
        Devuelve: correcta (bool), explicacion, opcion_correcta_id, estado
        """
        if estado.partida_terminada:
            return False, "La partida ya ha finalizado.", None, estado

        explicacion = ""
        opcion_correcta_id = None
        es_correcta = False

        # Usar banco en memoria si está disponible
        if banco_anom and (anomalia_id in banco_anom or str(anomalia_id) in banco_anom):
            info = banco_anom.get(anomalia_id) or banco_anom.get(str(anomalia_id))
            explicacion = info.get("explicacion", "")
            opcion_correcta_id = info.get("opcion_correcta_id")
            es_correcta = (int(opcion_id) == int(opcion_correcta_id)) if opcion_correcta_id is not None else False
        else:
            try:
                anomalia = AnomaliaAmbigua.objects.prefetch_related('opciones').get(id=anomalia_id)
            except AnomaliaAmbigua.DoesNotExist:
                return False, "Anomalía no encontrada.", None, estado

            try:
                opcion = anomalia.opciones.get(id=opcion_id)
            except OpcionMetrica.DoesNotExist:
                return False, "Opción no encontrada.", None, estado

            opcion_correcta = next((o for o in anomalia.opciones.all() if o.es_correcta), None)
            opcion_correcta_id = opcion_correcta.id if opcion_correcta else None
            explicacion = anomalia.explicacion
            es_correcta = opcion.es_correcta

        if es_correcta:
            # Correcta: puntaje += PUNTOS_ANOMALIA (plano) y combo sube
            estado.puntaje += cls.PUNTOS_ANOMALIA
            estado.combo = min(estado.combo + 1, cls.COMBO_MAXIMO)
            correcta = True
        else:
            # Incorrecta (RN-36): penalización y reinicio de combo
            estado.escudo = max(0, estado.escudo - cls.PENALIZACION_ESCUDO)
            estado.combo = cls.COMBO_INICIAL
            if estado.escudo <= 0:
                estado.escudo = 0
                estado.partida_terminada = True
            correcta = False

        return correcta, explicacion, opcion_correcta_id, estado

    @classmethod
    def penalizarEscudo(cls, motivo, estado):
        """
        Aplica penalización al escudo por eventos discretos.
        Motivos válidos: tiempo_agotado, no_interceptado, impacto_nave.
        """
        if motivo not in cls.MOTIVOS_VALIDOS:
            raise ValueError(f"Motivo de penalización no válido: '{motivo}'. Válidos: {cls.MOTIVOS_VALIDOS}")

        if estado.partida_terminada:
            return estado

        estado.escudo = max(0, estado.escudo - cls.PENALIZACION_ESCUDO)
        estado.combo = cls.COMBO_INICIAL
        if estado.escudo <= 0:
            estado.escudo = 0
            estado.partida_terminada = True

        return estado

    @classmethod
    def calcularPrecision(cls, estado, requerimientos_generados, banco_req=None):
        """
        requerimientos_generados: dict {requerimiento_id: veces_generado}
        El servidor consulta el tipo de cada id y suma los generados por tipo.
        Precisión por tipo = aciertos_tipo / generados_tipo * 100 (0 si no se generó ninguno).
        Precisión global = total de aciertos / total de generados * 100 (0 si total = 0).
        Las anomalías NO cuentan en la precisión.
        """
        generados_rf = 0
        generados_rnf = 0
        generados_rn = 0

        if requerimientos_generados and isinstance(requerimientos_generados, dict):
            req_ids = []
            for k in requerimientos_generados.keys():
                try:
                    req_ids.append(int(k))
                except (ValueError, TypeError):
                    pass

            if banco_req:
                req_map = {
                    int(r_id): info.get("tipo")
                    for r_id, info in banco_req.items()
                }
            else:
                req_map = {
                    r.id: r.tipo 
                    for r in Requerimiento.objects.filter(id__in=req_ids)
                }

            for k, veces in requerimientos_generados.items():
                try:
                    r_id = int(k)
                    v = max(0, int(veces))
                except (ValueError, TypeError):
                    continue

                tipo = req_map.get(r_id)
                if tipo == 'RF':
                    generados_rf += v
                elif tipo == 'RNF':
                    generados_rnf += v
                elif tipo == 'RN':
                    generados_rn += v

        total_generados = generados_rf + generados_rnf + generados_rn
        total_aciertos = estado.aciertos_rf + estado.aciertos_rnf + estado.aciertos_rn

        precision_rf = (estado.aciertos_rf / generados_rf * 100.0) if generados_rf > 0 else 0.0
        precision_rnf = (estado.aciertos_rnf / generados_rnf * 100.0) if generados_rnf > 0 else 0.0
        precision_rn = (estado.aciertos_rn / generados_rn * 100.0) if generados_rn > 0 else 0.0
        precision_global = (total_aciertos / total_generados * 100.0) if total_generados > 0 else 0.0

        return {
            'precision_global': round(precision_global, 1),
            'precision_rf': round(precision_rf, 1),
            'precision_rnf': round(precision_rnf, 1),
            'precision_rn': round(precision_rn, 1),
            'total_generados': total_generados,
            'generados_rf': generados_rf,
            'generados_rnf': generados_rnf,
            'generados_rn': generados_rn,
            'total_aciertos': total_aciertos,
            'aciertos_rf': estado.aciertos_rf,
            'aciertos_rnf': estado.aciertos_rnf,
            'aciertos_rn': estado.aciertos_rn,
        }

    @classmethod
    def calcularXP(cls, estado, precision_global):
        """
        xp = min(XP_MAXIMO, redondeo_half_up(0.5 * precision_global + 0.5 * min(100, puntaje * 100 / PUNTAJE_META)))
        """
        factor_puntaje = min(100.0, (estado.puntaje * 100.0) / cls.PUNTAGE_META if hasattr(cls, 'PUNTAGE_META') else (estado.puntaje * 100.0) / cls.PUNTAJE_META)
        val = 0.5 * float(precision_global) + 0.5 * factor_puntaje
        xp = cls.redondeo_half_up(val)
        return max(0, min(cls.XP_MAXIMO, xp))
