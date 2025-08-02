import httpx
from .config import get_settings
from sqlalchemy import text

settings = get_settings()

API_URL = "https://api.cerebras.net/v2/text"  # Correct as of Cerebras v2 API

HEADERS = {
    "Authorization": f"Bearer {settings.CEREBRAS_API_KEY}",
    "Content-Type": "application/json"
}

def extract_intent(tools_input: dict) -> str:
    return tools_input['prompt']

async def fetch_data(intent: str, db_session) -> str:
    result = await db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    )
    names = [row[0] for row in result]
    return f"# Available tables: {names}\n# Use pandas to load data from SQL."

def fetch_file_context(df) -> str:
    return f"# Data columns: {list(df.columns)}\n# Use pandas to analyze the DataFrame 'df'."

async def generate_plot_code(context: str, user_intent: str) -> str:
    prompt = f"""
You are a Python data visualization assistant. You can access a SQL database or a pandas DataFrame and plot data using pandas and matplotlib.
Context: {context}
User request: {user_intent}
Generate only executable Python code with matplotlib.
"""

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            API_URL,
            headers=HEADERS,
            json={
                "prompt": prompt,
                "max_tokens": 800,
                "temperature": 0.2,
            }
        )
        response.raise_for_status()
        return response.json()["text"]

async def run_workflow(prompt: str, db_session):
    """For database workflow only."""
    intent = extract_intent({'prompt': prompt})
    context = await fetch_data(intent, db_session)
    code = await generate_plot_code(context, intent)
    return code

async def run_workflow_file(prompt: str, df):
    """For file upload workflow only."""
    intent = extract_intent({'prompt': prompt})
    context = fetch_file_context(df)
    code = await generate_plot_code(context, intent)
    return code
