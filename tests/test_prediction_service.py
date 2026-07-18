import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.prediction_service import predict_and_reorder, resolve_llm_api_key


class PredictionServiceTests(unittest.TestCase):
    def test_resolve_llm_api_key_reads_env_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as handle:
            handle.write("GOOGLE_API_KEY=test-key-from-env\n")
            env_path = handle.name

        try:
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(resolve_llm_api_key(env_path=env_path), "test-key-from-env")
        finally:
            os.unlink(env_path)

    def test_predict_and_reorder_accepts_llm_api_key(self):
        scenario = {
            'product_name': 'Paracetamol',
            'category': 'Painkiller',
            'region': 'Tunis',
            'season': 'Winter',
            'event_type': 'Flu_Outbreak',
            'current_stock': 1200,
            'max_stock_capacity': 5000,
            'safety_stock': 400,
            'reserved_stock': 50,
            'avg_sales_7d': 80,
            'avg_sales_30d': 320,
            'avg_sales_90d': 900,
            'quantity_sold': 300,
            'number_of_orders': 40,
            'revenue': 12000,
            'returns': 2,
            'supplier_lead_time': 5,
            'supplier_reliability': 0.75,
            'month': 12,
            'quarter': 4,
            'holiday_indicator': 0,
            'impact_score': 80,
            'search_trend_score': 85.0,
            'news_signal_score': 8.2
        }

        with patch('scripts.prediction_service.requests.post', side_effect=RuntimeError('boom')):
            result = predict_and_reorder(scenario, llm_api_key='dummy-key')

        self.assertIn('explanation', result)
        self.assertTrue(result['explanation'])


if __name__ == '__main__':
    unittest.main()
