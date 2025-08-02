import pandas as pd
import os

class DataParser:
    @staticmethod
    def parse_file(file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            return pd.read_csv(file_path)
        elif ext in [".xlsx", ".xls"]:
            return pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file type")
