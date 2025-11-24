import csv
import os
from typing import Dict, Any, Optional

class MarketDataLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_data(self) -> Dict[str, Dict[str, float]]:
        """
        Loads market data from a CSV file.
        Expected columns: code, peg, eps_growth
        """
        data = {}
        if not os.path.exists(self.file_path):
            return data

        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get('code')
                    if not code:
                        continue

                    code = str(code).strip()
                    entry = {}

                    if row.get('peg'):
                        try:
                            val = row['peg'].strip()
                            if val:
                                entry['peg'] = float(val)
                        except ValueError:
                            pass

                    if row.get('eps_growth'):
                        try:
                            val = row['eps_growth'].strip()
                            if val:
                                entry['eps_growth'] = float(val)
                        except ValueError:
                            pass

                    if entry:
                        data[code] = entry

        except Exception as e:
            print(f"Warning: Failed to read market data file: {e}")

        return data
