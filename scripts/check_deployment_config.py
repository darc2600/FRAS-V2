from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "Dockerfile",
    "docker-compose.prod.yml",
    "requirements.txt",
    "nginx/default.conf",
    ".env.example",
]


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        print("Missing deployment files:")
        for path in missing:
            print(f"- {path}")
        return 1

    dockerfile = ROOT / "Dockerfile"
    try:
        dockerfile.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print("Dockerfile is not valid UTF-8.")
        return 1

    env_file = ROOT / ".env"
    if not env_file.exists():
        print(".env not found. Copy .env.example to .env and set JWT_SECRET before deployment.")
    else:
        env_text = env_file.read_text(encoding="utf-8", errors="ignore")
        if "JWT_SECRET=replace-this" in env_text or "JWT_SECRET=" not in env_text:
            print("JWT_SECRET is missing or still using the placeholder value.")
            return 1

    if not (ROOT / "attendance.db").exists():
        print("attendance.db not found. Add the demo database before running Docker.")
        return 1

    print("Deployment config check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
