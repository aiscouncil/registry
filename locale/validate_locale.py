#!/usr/bin/env python3
"""Validate a locale JSON file against en.json (the source of truth).

Usage:
    python3 registry/locale/validate_locale.py <locale_file.json>
    python3 registry/locale/validate_locale.py --all   # validate all locale files

Checks:
1. Valid JSON
2. All keys from en.json are present
3. No extra keys (typos)
4. Template variables {var} are preserved
5. _meta block is valid
"""

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
EN_PATH = SCRIPT_DIR / "en.json"

VAR_RE = re.compile(r"\{(\w+)\}")


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_vars(s: str) -> set:
    return set(VAR_RE.findall(s)) if isinstance(s, str) else set()


def validate(locale_path: Path, en: dict) -> list[str]:
    errors = []

    # 1. Valid JSON
    try:
        loc = load_json(locale_path)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    if not isinstance(loc, dict):
        return ["Root must be a JSON object"]

    # 2. Check _meta
    meta = loc.get("_meta", {})
    if not meta.get("lang"):
        errors.append("_meta.lang is missing")
    if not meta.get("name"):
        errors.append("_meta.name is missing")
    if meta.get("version") != en.get("_meta", {}).get("version"):
        errors.append(
            f"_meta.version mismatch: got {meta.get('version')}, expected {en['_meta']['version']}"
        )

    # 3. Missing keys
    en_keys = set(en.keys()) - {"_meta"}
    loc_keys = set(loc.keys()) - {"_meta"}

    missing = en_keys - loc_keys
    if missing:
        errors.append(f"Missing keys ({len(missing)}): {', '.join(sorted(missing))}")

    # 4. Extra keys
    extra = loc_keys - en_keys
    if extra:
        errors.append(f"Extra keys ({len(extra)}): {', '.join(sorted(extra))}")

    # 5. Template variables preserved
    for key in en_keys & loc_keys:
        en_vars = extract_vars(en[key])
        loc_vars = extract_vars(loc[key])
        if en_vars != loc_vars:
            missing_vars = en_vars - loc_vars
            extra_vars = loc_vars - en_vars
            parts = []
            if missing_vars:
                parts.append(f"missing {{{', '.join(missing_vars)}}}")
            if extra_vars:
                parts.append(f"extra {{{', '.join(extra_vars)}}}")
            errors.append(f"Key '{key}': template variable mismatch — {'; '.join(parts)}")

    # 6. Empty values (warn, not error)
    for key in en_keys & loc_keys:
        if isinstance(loc[key], str) and not loc[key].strip():
            errors.append(f"Key '{key}': empty value (untranslated?)")

    return errors


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <locale.json> | --all")
        sys.exit(1)

    en = load_json(EN_PATH)

    if sys.argv[1] == "--all":
        files = sorted(SCRIPT_DIR.glob("*.json"))
        files = [f for f in files if f.name != "en.json"]
        if not files:
            print("No locale files found (besides en.json)")
            sys.exit(0)
    else:
        files = [Path(sys.argv[1])]

    total_errors = 0
    for fp in files:
        errors = validate(fp, en)
        if errors:
            print(f"\n✗ {fp.name} — {len(errors)} issue(s):")
            for e in errors:
                print(f"  - {e}")
            total_errors += len(errors)
        else:
            print(f"✓ {fp.name} — OK")

    if total_errors:
        print(f"\n{total_errors} total issue(s) found.")
        sys.exit(1)
    else:
        print("\nAll locale files valid.")


if __name__ == "__main__":
    main()
