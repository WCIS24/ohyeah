import os
import subprocess
from datetime import datetime
from uuid import uuid4


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def utc_now_str() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def generate_run_id() -> str:
    return f"{utc_now_str()}_{uuid4().hex[:6]}"


def get_git_hash() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8").strip()
    except Exception:
        return "unknown"
