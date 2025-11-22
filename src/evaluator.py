import yaml
from typing import Dict, Any, List, Optional
from .models import FinancialData, EvaluationResult, AnalysisReport

class Evaluator:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

    def evaluate(self, current_data: FinancialData, last_year_data: Optional[FinancialData], stock_price: float) -> AnalysisReport:
        evaluations = []
        criteria = self.config['analysis']

        # --- P/L Analysis ---
        # Progress Rate (2Q check logic, but generalized)
        # If "2Q" is in fiscal_period or similar context, we could apply specific logic.
        # Here we just check against the default "good" threshold if forecast is available.
        if current_data.net_sales and current_data.forecast_net_sales:
            progress = (current_data.net_sales / current_data.forecast_net_sales) * 100
            assessment = "Bad"
            if progress >= criteria['pl']['progress_rate_2q']['good']:
                assessment = "Good"
            elif progress <= criteria['pl']['progress_rate_2q']['bad']:
                assessment = "Bad"
            else:
                assessment = "Neutral"

            evaluations.append(EvaluationResult(
                metric_name="通期進捗率(売上)",
                value=f"{progress:.2f}%",
                assessment=assessment,
                details=f"Forecast: {current_data.forecast_net_sales}"
            ))

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
            target = criteria['pl']['operating_margin']['default_target']
            assessment = "Good" if margin >= target else "Low" # Simplified logic
            evaluations.append(EvaluationResult(
                metric_name="営業利益率",
                value=f"{margin:.2f}%",
                assessment=assessment,
                details=f"Target (Gen): {target}%"
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

        # --- Cash Flow Analysis ---
        if current_data.operating_cf is not None and current_data.operating_profit is not None:
            assessment = "Good" if current_data.operating_cf > current_data.operating_profit else "Bad"
            evaluations.append(EvaluationResult(
                metric_name="営業CF > 営業利益",
                value=f"CF:{current_data.operating_cf} vs OP:{current_data.operating_profit}",
                assessment=assessment
            ))

        if current_data.operating_cf is not None and current_data.net_sales:
            ocf_margin = (current_data.operating_cf / current_data.net_sales) * 100
            op_margin = (current_data.operating_profit / current_data.net_sales) * 100 if current_data.operating_profit else 0
            assessment = "Good" if ocf_margin > op_margin else "Lower than OP Margin"
            evaluations.append(EvaluationResult(
                metric_name="営業CFマージン > 営業利益率",
                value=f"OCF%:{ocf_margin:.2f}% vs OP%:{op_margin:.2f}%",
                assessment=assessment
            ))

        if current_data.investment_cf is not None:
            assessment = "Normal" if current_data.investment_cf < 0 else "Attention (Positive)"
            evaluations.append(EvaluationResult(
                metric_name="投資CF",
                value=f"{current_data.investment_cf}",
                assessment=assessment
            ))

        if current_data.operating_cf is not None and current_data.investment_cf is not None:
            fcf = current_data.operating_cf + current_data.investment_cf  # Investment CF is usually negative
            assessment = "Positive" if fcf > 0 else "Negative"
            evaluations.append(EvaluationResult(
                metric_name="フリーキャッシュフロー(FCF)",
                value=f"{fcf}",
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

            forecast_net_sales=pl.get('forecast_net_sales'),
            forecast_operating_profit=pl.get('forecast_operating_profit'),
            forecast_net_income=pl.get('forecast_net_income'),

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
