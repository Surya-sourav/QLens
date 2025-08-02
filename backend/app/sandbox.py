import subprocess, tempfile, uuid
from pathlib import Path
from .config import get_settings
settings = get_settings()

BASE_SANDBOX_IMAGE = "python:3.10-slim"

def run_code_in_sandbox(code: str) -> Path:
    job_id = uuid.uuid4().hex
    work_dir = Path(tempfile.gettempdir()) / job_id
    work_dir.mkdir()
    script = work_dir / "script.py"
    script.write_text(code)

    result = subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{work_dir}:/app", BASE_SANDBOX_IMAGE,
        "timeout", f"{settings.SANDBOX_TIMEOUT}s",
        "python", "/app/script.py"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    # Expect script to save `output.png` in /app
    return work_dir / "output.png"