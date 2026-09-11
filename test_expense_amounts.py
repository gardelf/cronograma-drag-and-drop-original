import os
import unittest
from unittest.mock import patch

from expense_utils import extraer_monto_descripcion


class ExpenseAmountExtractionTests(unittest.TestCase):
    def extraer(self, texto):
        # Fuerza el analizador local que se usa si OpenAI no está disponible.
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('OPENAI_API_KEY', None)
            monto, descripcion, _, _, _ = extraer_monto_descripcion(texto)
        return monto, descripcion

    def test_importe_escrito_por_siri(self):
        self.assertEqual(self.extraer('cinco euros café'), (5.0, 'café'))

    def test_importe_escrito_sin_euros(self):
        self.assertEqual(self.extraer('cinco café'), (5.0, 'café'))

    def test_importe_compuesto(self):
        self.assertEqual(self.extraer('veinticinco euros Mercadona'), (25.0, 'Mercadona'))

    def test_decimales_con_con(self):
        self.assertEqual(self.extraer('cinco con cincuenta café'), (5.5, 'café'))

    def test_decimales_despues_de_euros(self):
        self.assertEqual(self.extraer('dos euros cincuenta café'), (2.5, 'café'))

    def test_formato_numerico_existente(self):
        self.assertEqual(self.extraer('5,50 café'), (5.5, 'café'))


if __name__ == '__main__':
    unittest.main()
