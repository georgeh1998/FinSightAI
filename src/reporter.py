import os
from datetime import datetime
from .models import AnalysisReport

class Reporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_markdown_report(self, report: AnalysisReport, stock_code: str, current_text: str = "", prev_text: str = ""):
        date_str = datetime.now().strftime('%Y-%m-%d')

        # Sanitize company name
        safe_company_name = "".join([c for c in report.company_name if c.isalnum() or c in (' ', '_', '-')]).strip()
        folder_name = f"{stock_code}_{safe_company_name}"

        report_dir = os.path.join(self.output_dir, folder_name, date_str)
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        filename = f"report.md"
        filepath = os.path.join(report_dir, filename)

        # Save extracted text
        if current_text:
            text_filename = "current_extracted_text.txt"
            with open(os.path.join(report_dir, text_filename), 'w', encoding='utf-8') as f:
                f.write(current_text)

        if prev_text:
            prev_text_filename = "previous_extracted_text.txt"
            with open(os.path.join(report_dir, prev_text_filename), 'w', encoding='utf-8') as f:
                f.write(prev_text)

        md = []
        md.append(f"# 企業分析レポート: {report.company_name}")
        md.append(f"**決算期**: {report.fiscal_period}")
        md.append(f"**現在株価**: {report.stock_price} 円")
        md.append(f"**分析日**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        md.append("")

        md.append("## 1. バリュエーション指標")
        if report.valuations:
            for k, v in report.valuations.items():
                md.append(f"- **{k}**: {v}")
        else:
            md.append("（データ不足のため算出不能）")
        md.append("")

        md.append("## 2. 定量分析結果 (基準照合)")
        md.append("| 項目 | 値 | 判定 | 詳細 |")
        md.append("|---|---|---|---|")
        for ev in report.evaluations:
            md.append(f"| {ev.metric_name} | {ev.value} | **{ev.assessment}** | {ev.details} |")
        md.append("")

        md.append("## 3. 定性分析・AI考察")
        qa = report.qualitative_analysis
        md.append("### 業績進捗")
        md.append(qa.get('progress_comment', ''))
        md.append("### 将来戦略")
        md.append(qa.get('future_strategy', ''))
        md.append("### リスク要因")
        md.append(qa.get('risk_factors', ''))
        md.append("### 経営陣の姿勢")
        md.append(qa.get('management_attitude', ''))
        md.append("### コスト効率性")
        md.append(qa.get('cost_efficiency', ''))

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(md))

        print(f"Report generated: {filepath}")
