# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

FinSightAI (10倍株発掘ツール / 10-Bagger Discovery Tool) is a Japanese financial analysis tool that uses AI to analyze quarterly financial reports (決算短信) from PDF documents. It extracts quantitative metrics and qualitative insights to evaluate potential high-growth stocks using criteria-based scoring.

## Running the Application

### Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"
```

### Running Analysis
```bash
python main.py
```

The tool prompts for:
- Stock code (証券コード, e.g., 8035)
- Current stock price (株価, e.g., 24000)

### Input File Convention
Place PDF files in the `input/` directory with naming format:
```
{code}_{year}_{quarter}.pdf
Example: 8035_2024_1Q.pdf
```

### Running Tests
```bash
python -m pytest tests/
# OR
python -m unittest tests/test_evaluator.py
```

## Architecture

### Pipeline Flow
The application follows a 4-stage pipeline:

1. **PDF Loading** (`pdf_loader.py`)
   - Finds financial reports matching the target stock code
   - Extracts text from PDFs using pdfminer.six
   - Automatically identifies latest and year-over-year comparison reports

2. **AI Analysis** (`ai_analyzer.py`)
   - Sends extracted text to OpenAI GPT-4o
   - Uses structured JSON output format to extract:
     - P/L metrics (売上高, 営業利益, 当期純利益, EPS, etc.)
     - B/S metrics (総資産, 純資産, 流動比率, 自己資本比率, etc.)
     - Cash flow data (営業CF, 投資CF, 財務CF)
     - Qualitative insights (management attitude, strategy, risk factors)

3. **Evaluation** (`evaluator.py`)
   - Maps AI-extracted JSON to structured `FinancialData` models
   - Compares current vs. previous year data for YoY analysis
   - Scores metrics against thresholds defined in `config/criteria.yaml`
   - Calculates valuation ratios (PER, PBR, PEG)
   - Assessment levels: "Top Class", "Excellent", "Pass", "Fail", "Ironclad", "Safe", "Danger", etc.

4. **Reporting** (`reporter.py`)
   - Generates markdown reports in `output/` directory
   - Filename format: `{company_name}_{date}.md`
   - Includes valuation metrics, quantitative scores, and qualitative AI commentary

### Key Data Models (`models.py`)

- **FinancialData**: Unified dataclass containing all P/L, B/S, CF, and qualitative fields
- **EvaluationResult**: Individual metric evaluation with assessment level
- **AnalysisReport**: Final report structure combining all analysis outputs

### Configuration (`config/criteria.yaml`)

Defines thresholds for:
- Revenue growth YoY (10%/20%/30% for Pass/Excellent/Top Class)
- Operating margin targets by industry
- B/S ratios (equity ratio, current ratio, D/E ratio)
- Valuation benchmarks (PER standard: 15x, PBR dissolution: 1x, PEG undervalued: <1x)
- Qualitative checkpoints

## Important Implementation Details

### AI Analyzer
- Uses GPT-4o with `response_format={"type": "json_object"}` to ensure valid JSON output
- Truncates input to 100,000 characters to avoid context limits
- Japanese prompt instructs model to act as securities analyst (証券アナリスト)
- Numbers should be numeric types, not strings (unit: 百万円 = millions of yen)

### Year-over-Year Comparison
The tool automatically compares the latest quarter with the same quarter from the previous year:
- Latest year/quarter determined by sorting reports
- Previous year = current year - 1, same quarter
- YoY analysis skipped if previous year data unavailable

### Evaluator Logic
- Metrics are evaluated conditionally based on data availability
- YoY calculations require both current and last_year_data
- Simplified industry-agnostic logic uses `default_target` values
- D/E ratio approximates equity as total_net_assets

### Output Location
- Markdown reports: `output/{company_name}_{YYYY-MM-DD}.md`
- Debug JSON (from AI): `sample.json` (written during execution at main.py:62-63)

## Development Notes

### Language
- Code comments and documentation are in Japanese (except this file)
- UI messages (print statements) are in Japanese
- Variable names are in English
- This is intentional for the Japanese market target audience

### Dependencies
- `openai`: For GPT-4o API access
- `pyyaml`: For loading criteria configuration
- `pdfminer.six`: For PDF text extraction

### Virtual Environment
The project uses `venv/` which is git-ignored. Always activate before running.
