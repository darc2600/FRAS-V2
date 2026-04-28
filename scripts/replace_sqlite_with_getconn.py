#!/usr/bin/env python3
"""
Scan selected runtime files and replace common sqlite3.connect patterns with get_connection().
Usage:
  python scripts/replace_sqlite_with_getconn.py --dry-run   # show changes
  python scripts/replace_sqlite_with_getconn.py --apply     # apply changes (backups saved as .bak)

It targets: backend.py, repositories/*.py, api/*.py, services/*.py (excluding this script and migration/test folders).
"""
import argparse
import re
from pathlib import Path

ROOT = Path('.')
TARGET_PATTERNS = [
    ROOT / 'backend.py',
]
# add globs
for d in ['repositories', 'api', 'services']:
    TARGET_PATTERNS.append(ROOT / d)

REPLACEMENTS = [
    # with sqlite3.connect(DB_PATH) as conn:
    (re.compile(r"with\s+sqlite3\.connect\(([^)]*)\)\s+as\s+(\w+):"),
     lambda m: f"with get_connection() as {m.group(2)}:"),
    # with sqlite3.connect('attendance.db') as conn:
    (re.compile(r"with\s+sqlite3\.connect\([^)]*\)\s+as\s+(\w+):"),
     lambda m: f"with get_connection() as {m.group(1)}:"),
    # conn = sqlite3.connect(...)
    (re.compile(r"(\w+)\s*=\s*sqlite3\.connect\([^\n\)]*\)"),
     lambda m: f"{m.group(1)} = get_connection()"),
]

IMPORT_INSERTION = 'from services.db import get_connection\n'

EXCLUDE_DIRS = {'scripts', '.venv', 'database', 'dataset', 'deployment', 'models', 'tests'}


def should_process(path: Path) -> bool:
    if not path.suffix == '.py':
        return False
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return False
    # only target files under our chosen dirs or backend.py at root
    if path.name == 'backend.py':
        return True
    if len(path.parts) >= 2 and path.parts[0] in {'repositories', 'api', 'services'}:
        return True
    return False


def process_file(path: Path, apply: bool=False):
    text = path.read_text(encoding='utf-8')
    original = text
    changed = False

    for pattern, repl in REPLACEMENTS:
        new_text = pattern.sub(repl, text)
        if new_text != text:
            changed = True
            text = new_text

    # Ensure import inserted if we replaced anything
    if changed and 'get_connection' in text and 'from services.db import get_connection' not in text:
        # insert after other imports or at top
        lines = text.splitlines()
        insert_at = 0
        for i, line in enumerate(lines[:40]):
            if line.startswith('import ') or line.startswith('from '):
                insert_at = i+1
        lines.insert(insert_at, IMPORT_INSERTION.rstrip('\n'))
        text = '\n'.join(lines) + ('\n' if text.endswith('\n') else '')

    if not changed:
        return False, []

    diffs = []
    # produce a small unified diff-like output
    orig_lines = original.splitlines()
    new_lines = text.splitlines()
    for i, (o, n) in enumerate(zip(orig_lines, new_lines)):
        if o != n:
            diffs.append((i+1, o, n))
    # account for added/removed tail lines
    if len(orig_lines) != len(new_lines):
        longer = new_lines if len(new_lines) > len(orig_lines) else orig_lines
        for i in range(min(len(orig_lines), len(new_lines)), len(longer)):
            if len(new_lines) > len(orig_lines):
                diffs.append((i+1, '', new_lines[i]))
            else:
                diffs.append((i+1, orig_lines[i], ''))

    if apply:
        bak = path.with_suffix(path.suffix + '.bak')
        path.write_text(original, encoding='utf-8') if not bak.exists() else None
        # save backup only if not exists
        if not bak.exists():
            path.write_text(original, encoding='utf-8')
            bak.write_text(original, encoding='utf-8')
        path.write_text(text, encoding='utf-8')

    return True, diffs


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    files = list(ROOT.rglob('*.py'))
    files = [f for f in files if should_process(f)]
    files.sort()

    changed_files = []
    for f in files:
        ok, diffs = process_file(f, apply=args.apply)
        if ok:
            changed_files.append((f, diffs))

    if not changed_files:
        print('No changes detected.')
        return

    for f, diffs in changed_files:
        print(f'--- {f}\n')
        for ln, old, new in diffs[:40]:
            print(f'{ln}: -{old}\n    +{new}')
        print('\n')

    print(f"{len(changed_files)} file(s) {'updated' if args.apply else 'would be updated'}.")

if __name__ == '__main__':
    main()
