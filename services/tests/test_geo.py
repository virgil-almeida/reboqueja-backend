import math

from django.test import SimpleTestCase

from services.geo import calcular_distancia, haversine_km


class HaversineTests(SimpleTestCase):
    def test_mesmo_ponto_retorna_zero(self):
        d = calcular_distancia(-19.9, -43.9, -19.9, -43.9)
        self.assertAlmostEqual(d, 0.0, places=6)

    def test_haversine_alias_igual_calcular_distancia(self):
        a = haversine_km(10.0, 20.0, -5.0, 40.0)
        b = calcular_distancia(10.0, 20.0, -5.0, 40.0)
        self.assertAlmostEqual(a, b, places=9)

    def test_polo_norte_antipoda_aproximadade_metade_meridiano(self):
        # (90,0) a (-90,0): meio círculo ~ π * R km
        d = calcular_distancia(90.0, 0.0, -90.0, 0.0)
        esperado = math.pi * 6371.0
        self.assertAlmostEqual(d, esperado, delta=1.0)

    def test_distancia_conhecida_curta(self):
        # ~111 km por grau de latitude no equador (ordem de grandeza)
        d = calcular_distancia(0.0, 0.0, 1.0, 0.0)
        self.assertGreater(d, 110.0)
        self.assertLess(d, 112.0)
