import unittest
from unittest.mock import patch

from firefly_client import FireflyClient


class RecurringTransfersTest(unittest.TestCase):
    def setUp(self):
        self.client = FireflyClient()

    def test_filters_by_month_direction_and_active_state(self):
        recurrences = {
            'data': [
                {
                    'attributes': {
                        'active': True,
                        'title': 'Aportación propiedad',
                        'repetitions': [{'type': 'monthly', 'moment': '2026-09-05'}],
                        'transactions': [
                            {'type': 'transfer', 'source_id': '6', 'destination_id': '7', 'amount': '250.50', 'description': 'Aportación'},
                            {'type': 'transfer', 'source_id': '7', 'destination_id': '6', 'amount': '900'},
                            {'type': 'transfer', 'source_id': '6', 'destination_id': '8', 'amount': '800'},
                            {'type': 'withdrawal', 'source_id': '6', 'destination_id': '7', 'amount': '700'},
                        ],
                    }
                },
                {
                    'attributes': {
                        'active': False,
                        'repetitions': [{'type': 'monthly', 'moment': '2026-09-01'}],
                        'transactions': [{'type': 'transfer', 'source_id': '6', 'destination_id': '7', 'amount': '600'}],
                    }
                },
                {
                    'attributes': {
                        'active': True,
                        'repetitions': [{'type': 'yearly', 'moment': '2026-10-01'}],
                        'transactions': [{'type': 'transfer', 'source_id': '6', 'destination_id': '7', 'amount': '500'}],
                    }
                },
            ]
        }

        with patch.object(self.client, '_make_request', return_value=recurrences):
            result = self.client.get_recurring_transfers_for_month(2026, 9, 6, 7)

        self.assertEqual(result['total'], 250.50)
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['description'], 'Aportación')

    def test_returns_empty_result_when_firefly_is_unavailable(self):
        with patch.object(self.client, '_make_request', side_effect=RuntimeError('offline')):
            result = self.client.get_recurring_transfers_for_month(2026, 9, 6, 7)

        self.assertEqual(result, {'items': [], 'total': 0.0})


if __name__ == '__main__':
    unittest.main()
