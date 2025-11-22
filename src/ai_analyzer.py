import os
import json
from openai import OpenAI
from typing import Dict, Any

class AIAnalyzer:
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Sends the extracted text to OpenAI API and asks it to extract
        key financial figures and qualitative information based on the criteria.
        """
        prompt = """
        あなたは熟練した証券アナリストです。以下の決算短信（または四半期報告書）のテキストデータから、
        投資分析に必要な定量的データと定性的情報を抽出し、JSON形式で出力してください。

        ## 抽出項目

        1. **基本情報 (basic_info)**
           - company_name: 会社名
           - fiscal_period: 決算期（例: 2024年3月期 第1四半期）

        2. **損益計算書データ (pl)**
           - net_sales: 売上高 (単位: 百万円)
           - operating_profit: 営業利益 (単位: 百万円)
           - ordinary_profit: 経常利益 (単位: 百万円)
           - net_income: 当期純利益 (単位: 百万円)
           - eps: 1株当たり当期純利益 (単位: 円)

        3. **貸借対照表データ (bs)**
           - total_assets: 総資産 (単位: 百万円)
           - total_net_assets: 純資産 (単位: 百万円)
           - current_assets: 流動資産 (単位: 百万円)
           - current_liabilities: 流動負債 (単位: 百万円)
           - quick_assets: 当座資産（流動資産 - 棚卸資産） (単位: 百万円, 棚卸資産が見つからない場合は流動資産の数値を使用し、注釈をつけること)
           - interest_bearing_debt: 有利子負債 (単位: 百万円)
           - equity_ratio: 自己資本比率 (%)
           - bps: 1株当たり純資産 (単位: 円)

        4. **キャッシュフローデータ (cf)**
           - operating_cf: 営業キャッシュフロー (単位: 百万円)
           - investment_cf: 投資キャッシュフロー (単位: 百万円)
           - financing_cf: 財務キャッシュフロー (単位: 百万円)
           - ※ 四半期決算短信などでCF計算書が省略されている場合は null または 0 とする。

        5. **定性情報 (qualitative)**
           - progress_comment: 業績進捗に関するコメント要約
           - future_strategy: 将来の戦略・見通しに関するコメント要約
           - risk_factors: 事業等のリスクに関する記述要約
           - management_attitude: 経営陣の姿勢（株主還元、主語が「私」か「私たち」かなど）に関する分析コメント
           - cost_efficiency_comment: 販管費の使用用途に関するコメント（研究開発、広告宣伝 vs 役員報酬、交際費など）

        ## 出力フォーマット
        必ず有効なJSON形式で出力してください。マークダウンのコードブロック（```json ... ```）で囲ってください。
        数値は文字列ではなく数値型（整数または浮動小数点数）で出力してください。単位が「百万円」のものは、テキストに記載されている数字をそのまま（例：12,345百万円なら 12345）出力してください。
        テキストデータが不完全で数値が見つからない場合は null を設定してください。

        ## テキストデータ
        """

        # Truncate text if it's too long to fit in context (rough handling)
        # 128k tokens is a lot, but let's be safe.
        truncated_text = text[:100000]

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful financial analyst assistant who outputs valid JSON."},
                {"role": "user", "content": prompt + "\n\n" + truncated_text}
            ],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        # Clean up potential markdown code blocks if response_format is not strictly enforced or behaves oddly
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print("Failed to decode JSON from AI response.")
            return {}
