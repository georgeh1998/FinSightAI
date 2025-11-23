import os
import re
from typing import List, Tuple, Optional
from pdfminer.high_level import extract_text

def extract_text_from_pdf(filepath: str) -> str:
    """
    Extracts text from a PDF file using pdfminer.six.
    """
    try:
        text = extract_text(filepath)
        return text
    except Exception as e:
        print(f"Error extracting text from {filepath}: {e}")
        return ""

def parse_filename(filename: str) -> Optional[Tuple[str, str, str]]:
    """
    Parses filename to extract code, year, and quarter.
    Expected format: {code}_{year}_{quarter}.pdf
    Example: 8035_2024_1Q.pdf -> ('8035', '2024', '1Q')
    """
    # Remove extension
    base = os.path.splitext(filename)[0]
    parts = base.split('_')
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    return None

def find_financial_reports(input_dir: str, target_code: str) -> dict:
    """
    Scans the input directory (recursively) for files matching the target code.
    Returns a dictionary organized by year/quarter.
    Structure:
    {
        '2024': {'1Q': 'path/to/file', ...},
        ...
    }
    """
    reports = {}
    if not os.path.exists(input_dir):
        return reports

    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if not filename.endswith(".pdf"):
                continue

            parsed = parse_filename(filename)
            if parsed:
                code, year, quarter = parsed
                if code == target_code:
                    if year not in reports:
                        reports[year] = {}
                    reports[year][quarter] = os.path.join(root, filename)

    return reports
