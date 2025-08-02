import os
from cerebras.cloud import Cerebras
from fastapi import HTTPException

client = Cerebras(api_key=os.getenv('CEREBRAS_API_KEY'))
SYSTEM = (
    "You are a Python data analysis assistant. You have access to a pandas DataFrame 'df'."
)

def generate_code(prompt: str, cols: list) -> str:
    msg = SYSTEM + f" DataFrame columns: {cols}."
    try:
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": msg},
                {"role": "user", "content": prompt}
            ],
            model="qwen-3-235b-a22b-instruct-2507"
        )
        code = resp.get('completion') or ''
        return code.strip()
    except Exception as e:
        raise HTTPException(500, f"LLM error: {e}")