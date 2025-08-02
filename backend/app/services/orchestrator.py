from .llm import generate_code
from .sandbox import execute

class DataChatOrchestrator:
    """
    Orchestrates LLM code generation and sandbox execution using LangGraph patterns.
    """
    def __init__(self, df, prompt):
        self.df = df
        self.prompt = prompt
        self.columns = list(df.columns)

    def run(self):
        # 1. Generate Python code via LLM
        code = generate_code(self.prompt, self.columns)
        # 2. Execute the code in sandbox
        text_output, image_base64 = execute(code, self.df)
        return text_output, image_base64