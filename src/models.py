from dataclasses import dataclass
from typing import Optional, List, Any

@dataclass
class FinancialData:
    # PL
    net_sales: Optional[float] = None
    operating_profit: Optional[float] = None
    ordinary_profit: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None

    # BS
    total_assets: Optional[float] = None
    total_net_assets: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    quick_assets: Optional[float] = None
    interest_bearing_debt: Optional[float] = None
    equity_ratio: Optional[float] = None
    bps: Optional[float] = None

    # CF
    operating_cf: Optional[float] = None
    investment_cf: Optional[float] = None
    financing_cf: Optional[float] = None

    # Qualitative
    progress_comment: str = ""
    future_strategy: str = ""
    risk_factors: str = ""
    management_attitude: str = ""
    cost_efficiency_comment: str = ""

    # Meta
    fiscal_period: str = ""
    company_name: str = ""

@dataclass
class EvaluationResult:
    metric_name: str
    value: Any
    assessment: str  # "Pass", "Excellent", "Bad", "Danger", etc.
    details: str = ""

@dataclass
class AnalysisReport:
    company_name: str
    fiscal_period: str
    stock_price: float
    evaluations: List[EvaluationResult]
    qualitative_analysis: dict
    valuations: dict
