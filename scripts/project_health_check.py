#!/usr/bin/env python3
"""
FRAS lightweight project health checker.

This script does not modify files. It checks for common repository issues before
opening a PR or preparing a demo.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    ".env.example",
    "backend.py",
    "attendance.db",
    "facial-attendance/package.json",
    "facial-attendance/src/app/login/login.component.ts",
    "facial-attendance/src/app/admin/analytics.component.ts",
    "facial-attendance/src/app/admin/attendance-reports/attendance-reports.component.ts",
    "docs/SETUP.md",
    "docs/DEPLOYMENT.md",
    "docs/DEMO_GUIDE.md",
    "docs/ROADMAP.md",
]

SENSITIVE_PATTERNS = [
    "ssh ",
    "password for postgress",
    "password for postgres",
    "JWT_SECRET=dev-secret-change-me",
    "your-secret-key-change-in-production",
]

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".angular",
    "dist",
    "build",
    "venv",
    ".venv",
    "__pycache__",
    "backups",
}

TEXT_EXTENSIONS = {
    ".py",
    ".ts",
    ".html",
    ".css",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".env",
    ".example",
    ".conf",
}


def exists_check() -> list[str]:
    issues: list[str] = []
    for rel in REQUIRED_PATHS:
        path = ROOT / rel
        if not path.exists():
            issues.append(f"Missing required file: {rel}")
    return issues


def dockerfile_encoding_check() -> list[str]:
    issues: list[str] = []
    dockerfile = ROOT / "Dockerfile"
    if not dockerfile.exists():
        return issues

    raw = dockerfile.read_bytes()
    if b"\x00" in raw[:200]:
        issues.append("Dockerfile appears to contain null bytes; it may be UTF-16 instead of UTF-8.")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        issues.append("Dockerfile is not valid UTF-8.")
    return issues


def env_check() -> list[str]:
    issues: list[str] = []
    env_file = ROOT / ".env"
    example_file = ROOT / ".env.example"

    if not example_file.exists():
        issues.append(".env.example is missing.")

    if env_file.exists():
        issues.append(".env exists locally. Make sure it is ignored and never committed.")

    return issues


def sensitive_text_check() -> list[str]:
    issues: list[str] = []
    for current_root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(current_root)
        for file_name in files:
            path = root_path / file_name
            suffix = path.suffix.lower()
            if suffix not in TEXT_EXTENSIONS and file_name not in {"Dockerfile", ".gitignore", ".dockerignore"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            rel = path.relative_to(ROOT).as_posix()
            for pattern in SENSITIVE_PATTERNS:
                if pattern.lower() in text:
                    issues.append(f"Possible sensitive/dev placeholder pattern found in {rel}: {pattern}")
    return issues


def main() -> int:
    checks = [
        ("Required files", exists_check),
        ("Dockerfile encoding", dockerfile_encoding_check),
        ("Environment files", env_check),
        ("Sensitive text scan", sensitive_text_check),
    ]

    all_issues: list[str] = []
    print("FRAS Project Health Check")
    print("=========================")
    print(f"Root: {ROOT}\n")

    for name, fn in checks:
        issues = fn()
        if issues:
            print(f"[WARN] {name}")
            for issue in issues:
                print(f"  - {issue}")
            print()
            all_issues.extend(issues)
        else:
            print(f"[OK] {name}")

    print()
    if all_issues:
        print(f"Completed with {len(all_issues)} warning(s). Review before demo or PR.")
        return 1

    print("No major health-check warnings found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
