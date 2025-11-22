import unittest
from src.models import FinancialData
from src.evaluator import Evaluator

class TestEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = Evaluator("config/criteria.yaml")

    def test_evaluate_yoy_growth(self):
        # Case 1: 30% Growth (Top Class)
        current = FinancialData(net_sales=1300, operating_profit=100)
        last = FinancialData(net_sales=1000, operating_profit=80)
        report = self.evaluator.evaluate(current, last, 1000)

        yoy_eval = next(e for e in report.evaluations if e.metric_name == "売上高成長率(YoY)")
        self.assertEqual(yoy_eval.assessment, "Top Class")
        self.assertEqual(yoy_eval.value, "30.00%")

        # Case 2: 15% Growth (Pass)
        current.net_sales = 1150
        report = self.evaluator.evaluate(current, last, 1000)
        yoy_eval = next(e for e in report.evaluations if e.metric_name == "売上高成長率(YoY)")
        self.assertEqual(yoy_eval.assessment, "Pass")

    def test_valuation(self):
        current = FinancialData(eps=100, bps=1000)
        stock_price = 1500
        report = self.evaluator.evaluate(current, None, stock_price)

        self.assertEqual(report.valuations['PER'], "15.00倍")
        self.assertEqual(report.valuations['PBR'], "1.50倍")

    def test_bs_metrics(self):
        # Equity Ratio 60% -> Ironclad
        current = FinancialData(equity_ratio=60.0)
        report = self.evaluator.evaluate(current, None, 1000)
        eq_eval = next(e for e in report.evaluations if e.metric_name == "自己資本比率")
        self.assertEqual(eq_eval.assessment, "Ironclad")

if __name__ == '__main__':
    unittest.main()
