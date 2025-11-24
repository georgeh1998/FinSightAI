import yaml
from typing import Dict, Any, Optional
from .models import FinancialData, EvaluationResult, AnalysisReport

class Evaluator:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

    def evaluate(self, current_data: FinancialData, last_year_data: Optional[FinancialData], stock_price: float) -> AnalysisReport:
        evaluations = []
        criteria = self.config['analysis']

        # --- P/L Analysis ---
        # YoY Sales Growth
        if current_data.net_sales and last_year_data and last_year_data.net_sales:
            growth = ((current_data.net_sales - last_year_data.net_sales) / last_year_data.net_sales) * 100

            assessment = "Fail"
            if growth >= criteria['pl']['revenue_growth_yoy']['thresholds']['top_class']:
                assessment = "Top Class"
            elif growth >= criteria['pl']['revenue_growth_yoy']['thresholds']['excellent']:
                assessment = "Excellent"
            elif growth >= criteria['pl']['revenue_growth_yoy']['thresholds']['pass']:
                assessment = "Pass"

            evaluations.append(EvaluationResult(
                metric_name="売上高成長率(YoY)",
                value=f"{growth:.2f}%",
                assessment=assessment
            ))

        # Operating Margin
        if current_data.net_sales and current_data.operating_profit:
            margin = (current_data.operating_profit / current_data.net_sales) * 100

            assessment = "Fail"
            if margin >= criteria['pl']['operating_margin']['thresholds']['top_class']:
                assessment = "Top Class"
            elif margin >= criteria['pl']['operating_margin']['thresholds']['excellent']:
                assessment = "Excellent"
            elif margin >= criteria['pl']['operating_margin']['thresholds']['pass']:
                assessment = "Pass"

            evaluations.append(EvaluationResult(
                metric_name="営業利益率",
                value=f"{margin:.2f}%",
                assessment=assessment
            ))

        # Operating Margin Improvement (YoY)
        if (current_data.net_sales and current_data.operating_profit and
            last_year_data and last_year_data.net_sales and last_year_data.operating_profit):
            current_margin = (current_data.operating_profit / current_data.net_sales) * 100
            last_year_margin = (last_year_data.operating_profit / last_year_data.net_sales) * 100
            margin_change = current_margin - last_year_margin

            assessment = "Improving" if margin_change > 0 else "Declining"
            evaluations.append(EvaluationResult(
                metric_name="営業利益率の改善(YoY)",
                value=f"{margin_change:+.2f}%pt",
                assessment=assessment,
                details=f"前年同期: {last_year_margin:.2f}% → 今期: {current_margin:.2f}%"
            ))

        # Progress Rate (Quarter-specific)
        quarter = self._extract_quarter(current_data.fiscal_period)
        if quarter and current_data.operating_profit and current_data.operating_profit_forecast:
            progress_rate = (current_data.operating_profit / current_data.operating_profit_forecast) * 100
            thresholds = criteria['pl']['progress_rate'].get(quarter, {})

            if thresholds:
                good_threshold = thresholds.get('good')
                bad_threshold = thresholds.get('bad')

                assessment = "Attention"
                if good_threshold and progress_rate >= good_threshold:
                    assessment = "Good"
                elif bad_threshold and progress_rate <= bad_threshold:
                    assessment = "Bad"

                evaluations.append(EvaluationResult(
                    metric_name=f"進捗率({quarter})",
                    value=f"{progress_rate:.1f}%",
                    assessment=assessment,
                    details=f"営業利益: {current_data.operating_profit:.0f}百万円 / 通期予想: {current_data.operating_profit_forecast:.0f}百万円"
                ))

        # --- B/S Analysis ---
        # Equity Ratio
        if current_data.equity_ratio:
            ratio = current_data.equity_ratio
            assessment = "Attention"
            if ratio >= criteria['bs']['capital_adequacy_ratio']['ironclad']:
                assessment = "Ironclad"
            elif ratio >= criteria['bs']['capital_adequacy_ratio']['safe']:
                assessment = "Safe"

            evaluations.append(EvaluationResult(
                metric_name="自己資本比率",
                value=f"{ratio:.2f}%",
                assessment=assessment
            ))

        # Current Ratio
        if current_data.current_assets and current_data.current_liabilities:
            ratio = (current_data.current_assets / current_data.current_liabilities) * 100
            assessment = "Danger"
            if ratio >= criteria['bs']['current_ratio']['very_safe']:
                assessment = "Very Safe"
            elif ratio >= criteria['bs']['current_ratio']['safe']:
                assessment = "Safe"
            elif ratio >= criteria['bs']['current_ratio']['danger']:
                assessment = "OK"

            evaluations.append(EvaluationResult(
                metric_name="流動比率",
                value=f"{ratio:.2f}%",
                assessment=assessment
            ))

        # D/E Ratio
        if current_data.interest_bearing_debt is not None and current_data.total_net_assets:
            # Approximating Equity as Total Net Assets for simplicity, though technically Equity = Net Assets - Minority Interests
            ratio = current_data.interest_bearing_debt / current_data.total_net_assets
            assessment = "Danger"
            if ratio <= criteria['bs']['de_ratio']['very_safe']:
                assessment = "Very Safe"
            elif ratio <= criteria['bs']['de_ratio']['healthy']:
                assessment = "Healthy"
            elif ratio <= criteria['bs']['de_ratio']['danger']:
                assessment = "Caution"

            evaluations.append(EvaluationResult(
                metric_name="D/Eレシオ",
                value=f"{ratio:.2f}倍",
                assessment=assessment
            ))

        # --- Valuation ---
        vals = {}
        if current_data.eps:
            per = stock_price / current_data.eps
            vals['PER'] = f"{per:.2f}倍"

        if current_data.bps:
            pbr = stock_price / current_data.bps
            vals['PBR'] = f"{pbr:.2f}倍"

        # PEG Ratio (PER / Growth Rate)
        if current_data.eps and last_year_data and last_year_data.eps and last_year_data.eps > 0:
             eps_growth = ((current_data.eps - last_year_data.eps) / last_year_data.eps) * 100
             if eps_growth > 0 and 'PER' in vals:
                 # Recalculate PER numerical value
                 per_val = stock_price / current_data.eps
                 peg = per_val / eps_growth
                 vals['PEG'] = f"{peg:.2f}倍"

        qual_analysis = {
            "progress_comment": current_data.progress_comment,
            "future_strategy": current_data.future_strategy,
            "risk_factors": current_data.risk_factors,
            "management_attitude": current_data.management_attitude,
            "cost_efficiency": current_data.cost_efficiency_comment
        }

        return AnalysisReport(
            company_name=current_data.company_name,
            fiscal_period=current_data.fiscal_period,
            stock_price=stock_price,
            evaluations=evaluations,
            qualitative_analysis=qual_analysis,
            valuations=vals
        )

    def _extract_quarter(self, fiscal_period: str) -> Optional[str]:
        """決算期から四半期を抽出 (例: '2024年12月期 第1四半期' -> '1Q')"""
        if not fiscal_period:
            return None

        if '第1四半期' in fiscal_period or '1Q' in fiscal_period:
            return '1Q'
        elif '第2四半期' in fiscal_period or '2Q' in fiscal_period or '中間' in fiscal_period:
            return '2Q'
        elif '第3四半期' in fiscal_period or '3Q' in fiscal_period:
            return '3Q'
        elif '通期' in fiscal_period or '本決算' in fiscal_period or '期末' in fiscal_period:
            return '通期'

        return None

    def map_json_to_model(self, data: Dict[str, Any]) -> FinancialData:
        pl = data.get('pl', {})
        bs = data.get('bs', {})
        cf = data.get('cf', {})
        ql = data.get('qualitative', {})
        basic = data.get('basic_info', {})

        return FinancialData(
            net_sales=pl.get('net_sales'),
            operating_profit=pl.get('operating_profit'),
            ordinary_profit=pl.get('ordinary_profit'),
            net_income=pl.get('net_income'),
            eps=pl.get('eps'),
            operating_profit_forecast=pl.get('operating_profit_forecast'),

            total_assets=bs.get('total_assets'),
            total_net_assets=bs.get('total_net_assets'),
            current_assets=bs.get('current_assets'),
            current_liabilities=bs.get('current_liabilities'),
            quick_assets=bs.get('quick_assets'),
            interest_bearing_debt=bs.get('interest_bearing_debt'),
            equity_ratio=bs.get('equity_ratio'),
            bps=bs.get('bps'),

            operating_cf=cf.get('operating_cf'),
            investment_cf=cf.get('investment_cf'),
            financing_cf=cf.get('financing_cf'),

            progress_comment=ql.get('progress_comment', ""),
            future_strategy=ql.get('future_strategy', ""),
            risk_factors=ql.get('risk_factors', ""),
            management_attitude=ql.get('management_attitude', ""),
            cost_efficiency_comment=ql.get('cost_efficiency_comment', ""),

            company_name=basic.get('company_name', "Unknown"),
            fiscal_period=basic.get('fiscal_period', "Unknown")
        )
