from django.test import SimpleTestCase
from dashboard.services.analytics import wilson
class WilsonTests(SimpleTestCase):
    def test_known_interval(self):
        low,high=wilson(218,397)
        self.assertAlmostEqual(low,50.0,places=1)
        self.assertAlmostEqual(high,59.7,places=1)
