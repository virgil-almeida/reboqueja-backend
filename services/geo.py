from math import asin, cos, radians, sin, sqrt

_EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Cálculo Haversine interno (km). Preferir `calcular_distancia` na API pública."""
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    rlat1, rlon1, rlat2, rlon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    h = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * asin(min(1.0, sqrt(h)))


def calcular_distancia(lat1, lng1, lat2, lng2) -> float:
    """
    Distância em quilômetros entre dois pontos (latitude/longitude em graus decimais).
    Usa fórmula de Haversine; integrada na listagem de solicitações e prestadores.
    """
    return haversine_km(lat1, lng1, lat2, lng2)
