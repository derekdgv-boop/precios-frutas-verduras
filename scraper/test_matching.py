"""Tests del emparejamiento producto↔catálogo, la parte más frágil del scraper.

Correr desde la raíz del repo:
    python -m unittest discover -s scraper -p "test_*.py"
o simplemente:
    python scraper/test_matching.py

No hacen red: solo prueban la lógica de regex (build_pattern) y de selección
de canasta (match_basket) con datos en memoria.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generar_products import build_pattern
from run import match_basket, normalize
import re


def _catalogo(**items):
    """Construye un catálogo {canon: {"nombre", "patron"}} desde keywords."""
    return {
        canon: {"nombre": canon, "patron": build_pattern(kws)}
        for canon, kws in items.items()
    }


class TestBuildPattern(unittest.TestCase):
    def _match(self, keywords, nombre):
        rx = re.compile(build_pattern(keywords))
        return bool(rx.search(normalize(nombre)))

    def test_plural_si_matchea(self):
        self.assertTrue(self._match(["cana"], "Caña"))
        self.assertTrue(self._match(["cana"], "Cañas de azúcar"))

    def test_prefijo_no_matchea(self):
        # 's?' (no '\\w*'): "cana" NO debe atrapar "canario".
        self.assertFalse(self._match(["cana"], "Alpiste canario"))

    def test_palabra_prohibida_excluye(self):
        # ciruela roja = ["ciruela", "!moscatel"]
        kws = ["ciruela", "!moscatel"]
        self.assertTrue(self._match(kws, "Ciruela Roja"))
        self.assertFalse(self._match(kws, "Ciruela Moscatel"))

    def test_multiples_palabras_cualquier_orden(self):
        kws = ["jitomate|tomate", "saladet"]
        self.assertTrue(self._match(kws, "Saladet Jitomate por Kg"))
        self.assertTrue(self._match(kws, "Tomate Saladet"))
        self.assertFalse(self._match(kws, "Jitomate Bola"))

    def test_alternancia(self):
        kws = ["arandano|blueberry"]
        self.assertTrue(self._match(kws, "Blueberry Fresco"))
        self.assertTrue(self._match(kws, "Arándano azul"))


class TestMatchBasket(unittest.TestCase):
    def test_kg_gana_aunque_sea_mas_caro(self):
        cat = _catalogo(aguacate=["aguacate"])
        productos = [
            {"nombre": "Aguacate paquete 250g", "precio": 20.0, "unidad": "pza"},
            {"nombre": "Aguacate Hass por Kg", "precio": 59.5, "unidad": "kg"},
        ]
        elegido = match_basket(productos, cat)["aguacate"]
        self.assertEqual(elegido["unidad"], "kg")
        self.assertEqual(elegido["precio"], 59.5)

    def test_mas_barato_cuando_ninguno_es_kg(self):
        cat = _catalogo(acelga=["acelga"])
        productos = [
            {"nombre": "Acelga Rollo", "precio": 15.0, "unidad": "un"},
            {"nombre": "Acelga Verde", "precio": 9.9, "unidad": "un"},
        ]
        elegido = match_basket(productos, cat)["acelga"]
        self.assertEqual(elegido["precio"], 9.9)

    def test_sin_match_no_aparece(self):
        cat = _catalogo(mango=["mango"])
        productos = [{"nombre": "Papaya Maradol", "precio": 25.0, "unidad": "kg"}]
        self.assertNotIn("mango", match_basket(productos, cat))


if __name__ == "__main__":
    unittest.main(verbosity=2)
