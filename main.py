import sys
import os
from src.pdf_loader import find_financial_reports, extract_text_from_pdf
from src.ai_analyzer import AIAnalyzer
from src.evaluator import Evaluator
from src.reporter import Reporter

def main():
    print("=== 10倍株発掘ツール ===")

    # 1. User Input
    stock_code = input("証券コードを入力してください (例: 8035): ").strip()
    stock_price_input = input("現在の株価を入力してください (例: 24000): ").strip()

    try:
        stock_price = float(stock_price_input)
    except ValueError:
        print("株価は数値で入力してください。")
        return

    # 2. Find Files
    reports_map = find_financial_reports("input", stock_code)
    if not reports_map:
        print(f"エラー: inputディレクトリにコード {stock_code} のPDFが見つかりません。")
        print("命名規則: {code}_{year}_{quarter}.pdf (例: 8035_2024_1Q.pdf)")
        return

    # Sort years to find the latest and previous
    years = sorted(reports_map.keys(), reverse=True)
    latest_year = years[0]
    # Assuming we want to compare same quarter of latest year vs previous year
    # Let's ask user or pick the latest available quarter in the latest year
    latest_quarters = sorted(reports_map[latest_year].keys(), reverse=True)
    target_quarter = latest_quarters[0]

    current_pdf_path = reports_map[latest_year][target_quarter]
    print(f"最新のレポート: {current_pdf_path} ({latest_year} {target_quarter}) を読み込み中...")

    # Find Previous Year Same Quarter
    prev_year = str(int(latest_year) - 1)
    prev_pdf_path = None
    if prev_year in reports_map and target_quarter in reports_map[prev_year]:
        prev_pdf_path = reports_map[prev_year][target_quarter]
        print(f"昨年のレポート: {prev_pdf_path} ({prev_year} {target_quarter}) を読み込み中...")
    else:
        print(f"昨年のレポートが見つかりません ({prev_year} {target_quarter})。YoY分析はスキップされます。")

    # 3. Processing
    analyzer = AIAnalyzer()
    evaluator = Evaluator("config/criteria.yaml")
    reporter = Reporter("output")

    # Extract & Analyze Current
    current_text = extract_text_from_pdf(current_pdf_path)
    if not current_text:
        print("PDFからテキストを抽出できませんでした。")
        return

    print("AIによる解析を実行中 (最新)...")
    current_json = analyzer.analyze_text(current_text)
    current_data = evaluator.map_json_to_model(current_json)

    # Extract & Analyze Previous (if exists)
    last_year_data = None
    prev_text = ""
    if prev_pdf_path:
        prev_text = extract_text_from_pdf(prev_pdf_path)
        if prev_text:
            print("AIによる解析を実行中 (昨年)...")
            prev_json = analyzer.analyze_text(prev_text)
            last_year_data = evaluator.map_json_to_model(prev_json)

    # 4. Evaluate & Report
    print("データを評価中...")
    report = evaluator.evaluate(current_data, last_year_data, stock_price)

    reporter.generate_markdown_report(report, stock_code, current_text, prev_text)
    print("\n完了しました。outputフォルダを確認してください。")

if __name__ == "__main__":
    main()
