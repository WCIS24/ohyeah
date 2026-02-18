from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime
from importlib import metadata
from typing import Dict, Iterable, Optional
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


def _package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not_installed"
    except Exception:
        return "unknown"


def collect_env_versions(packages: Optional[Iterable[str]] = None) -> Dict[str, str]:
    package_list = list(packages) if packages is not None else [
        "numpy",
        "pandas",
        "pyyaml",
        "scikit-learn",
        "datasets",
        "rank-bm25",
        "sentence-transformers",
        "torch",
        "transformers",
    ]
    versions: Dict[str, str] = {
        "python": platform.python_version(),
    }
    for name in package_list:
        versions[name] = _package_version(name)
    return versions


def write_env_versions(run_dir: str, packages: Optional[Iterable[str]] = None) -> str:
    ensure_dir(run_dir)
    out_path = os.path.join(run_dir, "env_versions.json")
    versions = collect_env_versions(packages=packages)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2, sort_keys=True)
    return out_path
