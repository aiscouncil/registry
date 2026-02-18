#!/usr/bin/env python3
"""Validate registry/models.json and registry/packages.json for aiscouncil."""
import json
import re
import sys
from pathlib import Path

REQUIRED_MODEL_FIELDS = {"id", "name", "provider", "context", "maxOutput", "pricing", "capabilities", "tier"}
ALLOWED_CAPABILITIES = {"vision", "tools", "streaming", "json_mode", "reasoning", "code"}
ALLOWED_TIERS = {"free", "paid", "enterprise"}
REQUIRED_PROVIDER_FIELDS = {"name", "baseUrl", "authType", "format"}

# Package registry constants
ALLOWED_PACKAGE_TYPES = {"plugin", "addon", "mini-program"}
ALLOWED_REGISTRY_TIERS = {"community", "ai-verified", "verified", "platform"}
ALLOWED_VERIFICATION_TIERS = {"quick", "full", "deep"}
HASH_RE = re.compile(r'^[0-9a-f]{64}$')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}')
JOB_ID_RE = re.compile(r'^ver_[a-zA-Z0-9]+$')
ALLOWED_PERMISSIONS = {
    "storage", "chat:read", "chat:write", "config:read", "config:write",
    "auth:read", "ui:toast", "ui:modal", "hooks:action", "hooks:filter",
    "network:fetch", "secrets:sync"
}
NAME_RE = re.compile(r'^[a-z0-9-]+$')
VERSION_RE = re.compile(r'^\d+\.\d+\.\d+')


def validate(path: str = None) -> list[str]:
    """Validate the model registry. Returns list of error strings."""
    if path is None:
        path = Path(__file__).parent / "models.json"
    else:
        path = Path(path)

    errors = []

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return [f"File not found: {path}"]

    # Top-level fields
    if "version" not in data:
        errors.append("Missing top-level 'version' field")
    if "providers" not in data:
        errors.append("Missing 'providers' object")
        return errors
    if "models" not in data:
        errors.append("Missing 'models' array")
        return errors

    providers = data["providers"]
    models = data["models"]

    # Validate providers
    for pid, prov in providers.items():
        missing = REQUIRED_PROVIDER_FIELDS - set(prov.keys())
        if missing:
            errors.append(f"Provider '{pid}' missing fields: {missing}")

    # Validate models
    seen_ids = set()
    for i, model in enumerate(models):
        prefix = f"Model [{i}] '{model.get('id', '?')}'"

        # Required fields
        missing = REQUIRED_MODEL_FIELDS - set(model.keys())
        if missing:
            errors.append(f"{prefix}: missing fields: {missing}")
            continue

        # Duplicate IDs
        if model["id"] in seen_ids:
            errors.append(f"{prefix}: duplicate model ID")
        seen_ids.add(model["id"])

        # Provider exists
        if model["provider"] not in providers:
            errors.append(f"{prefix}: unknown provider '{model['provider']}'")

        # Tier valid
        if model["tier"] not in ALLOWED_TIERS:
            errors.append(f"{prefix}: invalid tier '{model['tier']}' (allowed: {ALLOWED_TIERS})")

        # Capabilities valid
        invalid_caps = set(model["capabilities"]) - ALLOWED_CAPABILITIES
        if invalid_caps:
            errors.append(f"{prefix}: invalid capabilities {invalid_caps}")

        # Pricing non-negative
        pricing = model.get("pricing", {})
        if pricing.get("input", 0) < 0 or pricing.get("output", 0) < 0:
            errors.append(f"{prefix}: pricing must be non-negative")

        # Context/maxOutput positive
        if model["context"] <= 0:
            errors.append(f"{prefix}: context must be positive")
        if model["maxOutput"] <= 0:
            errors.append(f"{prefix}: maxOutput must be positive")

    # Validate presetCouncils
    VALID_COUNCIL_STYLES = {"research", "compare", "arena", "moa", "router", "debate", "consensus"}
    NEEDS_CHAIRMAN = {"research", "moa", "router", "debate"}
    if "presetCouncils" in data:
        pcs = data["presetCouncils"]
        if not isinstance(pcs, list):
            errors.append("'presetCouncils' must be an array")
        else:
            for i, pc in enumerate(pcs):
                prefix = f"PresetCouncil [{i}] '{pc.get('name', '?')}'"
                if not isinstance(pc, dict):
                    errors.append(f"PresetCouncil [{i}]: must be an object")
                    continue
                for req in ("name", "style", "members"):
                    if req not in pc:
                        errors.append(f"{prefix}: missing '{req}'")
                if "style" in pc and pc["style"] not in VALID_COUNCIL_STYLES:
                    errors.append(f"{prefix}: invalid style '{pc['style']}' (allowed: {VALID_COUNCIL_STYLES})")
                if "simpleDescription" in pc and not isinstance(pc["simpleDescription"], str):
                    errors.append(f"{prefix}: simpleDescription must be a string")
                if "chairman" in pc:
                    ch = pc["chairman"]
                    if ch is not None and not isinstance(ch, int):
                        errors.append(f"{prefix}: chairman must be an integer or null")
                    elif isinstance(ch, int) and "members" in pc and isinstance(pc["members"], list):
                        if ch < 0 or ch >= len(pc["members"]):
                            errors.append(f"{prefix}: chairman index {ch} out of range (0-{len(pc['members'])-1})")
                if "members" in pc:
                    if not isinstance(pc["members"], list) or len(pc["members"]) < 2:
                        errors.append(f"{prefix}: members must be an array with at least 2 entries")
                    else:
                        for j, m in enumerate(pc["members"]):
                            if not isinstance(m, dict):
                                errors.append(f"{prefix} member [{j}]: must be an object")
                            elif "provider" not in m or "model" not in m:
                                errors.append(f"{prefix} member [{j}]: missing 'provider' or 'model'")

    return errors


def validate_manifest(manifest: dict) -> list[str]:
    """Validate a single manifest v2 object. Returns list of error strings."""
    errors = []
    prefix = f"Manifest '{manifest.get('name', '?')}'"

    # Required fields
    if "name" not in manifest:
        errors.append(f"{prefix}: missing 'name'")
    elif not NAME_RE.match(manifest["name"]):
        errors.append(f"{prefix}: name must match ^[a-z0-9-]+$ (got '{manifest['name']}')")
    elif len(manifest["name"]) > 64:
        errors.append(f"{prefix}: name exceeds 64 characters")

    if "version" not in manifest:
        errors.append(f"{prefix}: missing 'version'")
    elif not VERSION_RE.match(manifest["version"]):
        errors.append(f"{prefix}: version must be semver (got '{manifest['version']}')")

    # ABI version
    if "abi" in manifest and manifest["abi"] != 1:
        errors.append(f"{prefix}: abi must be 1 (got {manifest['abi']})")

    # Type
    pkg_type = manifest.get("type", "plugin")
    if pkg_type not in ALLOWED_PACKAGE_TYPES:
        errors.append(f"{prefix}: invalid type '{pkg_type}' (allowed: {ALLOWED_PACKAGE_TYPES})")

    # Type-specific requirements
    if pkg_type == "mini-program":
        if "entry" not in manifest:
            errors.append(f"{prefix}: mini-program requires 'entry' field")
        if "base_url" not in manifest:
            errors.append(f"{prefix}: mini-program requires 'base_url' field")
    elif pkg_type == "plugin":
        if "wasm" not in manifest:
            errors.append(f"{prefix}: plugin requires 'wasm' field")
        if "wasm_sha256" not in manifest:
            errors.append(f"{prefix}: plugin requires 'wasm_sha256' field")
        elif manifest.get("wasm_sha256") and not re.match(r'^[0-9a-f]{64}$', manifest["wasm_sha256"]):
            errors.append(f"{prefix}: wasm_sha256 must be 64 hex characters")
    elif pkg_type == "addon":
        if "wasm" not in manifest and "entry" not in manifest:
            errors.append(f"{prefix}: addon requires either 'wasm' or 'entry' field")

    # Permissions
    if "permissions" in manifest:
        if not isinstance(manifest["permissions"], list):
            errors.append(f"{prefix}: permissions must be an array")
        else:
            invalid = set(manifest["permissions"]) - ALLOWED_PERMISSIONS
            if invalid:
                errors.append(f"{prefix}: invalid permissions {invalid}")

    # Description length
    if "description" in manifest and len(manifest["description"]) > 256:
        errors.append(f"{prefix}: description exceeds 256 characters")

    # Keywords
    if "keywords" in manifest:
        if not isinstance(manifest["keywords"], list):
            errors.append(f"{prefix}: keywords must be an array")
        elif len(manifest["keywords"]) > 10:
            errors.append(f"{prefix}: max 10 keywords allowed")

    return errors


def validate_packages(path: str = None) -> list[str]:
    """Validate the package registry. Returns list of error strings."""
    if path is None:
        path = Path(__file__).parent / "packages.json"
    else:
        path = Path(path)

    errors = []

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return [f"File not found: {path}"]

    if "version" not in data:
        errors.append("Missing top-level 'version' field")
    if "packages" not in data:
        errors.append("Missing 'packages' array")
        return errors

    packages = data["packages"]
    if not isinstance(packages, list):
        errors.append("'packages' must be an array")
        return errors

    seen_names = set()
    for i, pkg in enumerate(packages):
        prefix = f"Package [{i}] '{pkg.get('name', '?')}'"

        if not isinstance(pkg, dict):
            errors.append(f"Package [{i}]: must be an object")
            continue

        # Required registry fields
        if "name" not in pkg:
            errors.append(f"{prefix}: missing 'name'")
        elif pkg["name"] in seen_names:
            errors.append(f"{prefix}: duplicate package name")
        else:
            seen_names.add(pkg["name"])

        if "type" not in pkg:
            errors.append(f"{prefix}: missing 'type'")
        elif pkg["type"] not in ALLOWED_PACKAGE_TYPES:
            errors.append(f"{prefix}: invalid type '{pkg['type']}'")

        if "version" not in pkg:
            errors.append(f"{prefix}: missing 'version'")
        elif not VERSION_RE.match(pkg["version"]):
            errors.append(f"{prefix}: version must be semver")

        if "manifest" not in pkg:
            errors.append(f"{prefix}: missing 'manifest' URL")

        # Marketplace tier
        if "tier" in pkg:
            if pkg["tier"] not in ALLOWED_REGISTRY_TIERS:
                errors.append(f"{prefix}: invalid tier '{pkg['tier']}' (allowed: {ALLOWED_REGISTRY_TIERS})")

        # Pricing
        if "price" in pkg:
            if not isinstance(pkg["price"], (int, float)):
                errors.append(f"{prefix}: price must be a number (cents)")
            elif pkg["price"] < 0:
                errors.append(f"{prefix}: price must be non-negative")
            # Paid apps need a seller (null = platform-owned, allowed)
            if pkg.get("price", 0) > 0 and "seller" not in pkg:
                errors.append(f"{prefix}: paid packages require a 'seller' field (null for platform-owned, or {{name, id}} for third-party)")

        # Seller
        if "seller" in pkg and pkg["seller"] is not None:
            seller = pkg["seller"]
            if not isinstance(seller, dict):
                errors.append(f"{prefix}: seller must be an object or null")
            else:
                if "name" not in seller:
                    errors.append(f"{prefix}: seller missing 'name'")
                if "id" not in seller:
                    errors.append(f"{prefix}: seller missing 'id'")

        # Verification badge
        if "verification" in pkg:
            v = pkg["verification"]
            if not isinstance(v, dict):
                errors.append(f"{prefix}: verification must be an object")
            else:
                if "hash" not in v:
                    errors.append(f"{prefix}: verification missing 'hash'")
                elif not HASH_RE.match(v["hash"]):
                    errors.append(f"{prefix}: verification hash must be 64 hex characters")
                if "tier" not in v:
                    errors.append(f"{prefix}: verification missing 'tier'")
                elif v["tier"] not in ALLOWED_VERIFICATION_TIERS:
                    errors.append(f"{prefix}: invalid verification tier '{v['tier']}' (allowed: {ALLOWED_VERIFICATION_TIERS})")
                if "date" not in v:
                    errors.append(f"{prefix}: verification missing 'date'")
                elif not DATE_RE.match(v["date"]):
                    errors.append(f"{prefix}: verification date must be ISO 8601 (YYYY-MM-DD)")
                if "expires" not in v:
                    errors.append(f"{prefix}: verification missing 'expires'")
                elif not DATE_RE.match(v["expires"]):
                    errors.append(f"{prefix}: verification expires must be ISO 8601 (YYYY-MM-DD)")
                if "job_id" not in v:
                    errors.append(f"{prefix}: verification missing 'job_id'")
                elif not JOB_ID_RE.match(v["job_id"]):
                    errors.append(f"{prefix}: verification job_id must match ver_[a-zA-Z0-9]+")

            # ai-verified tier requires verification object
        if pkg.get("tier") == "ai-verified" and "verification" not in pkg:
            errors.append(f"{prefix}: ai-verified tier requires a 'verification' object")

        # Platform tier: seller must be null (platform-owned)
        if pkg.get("tier") == "platform":
            if "seller" in pkg and pkg["seller"] is not None:
                errors.append(f"{prefix}: platform tier requires seller to be null (platform-owned)")

        # Category validation
        if "category" in pkg:
            if not isinstance(pkg["category"], str):
                errors.append(f"{prefix}: category must be a string")

    return errors


CSS_PROP_NAME_RE = re.compile(r'^--[a-z][-a-z0-9]+$')
CSS_FORBIDDEN_VALUES = re.compile(r'url\s*\(|expression\s*\(|javascript:|@import', re.IGNORECASE)
XSS_FORBIDDEN = re.compile(r'<script|onclick|onerror|onload|javascript:', re.IGNORECASE)
VALID_SIDEBAR_PANELS = {"left", "chat", "right"}
VALID_WELCOME_ACTIONS = {"focus-input", "open-config", "new-council", "open-settings"}


def validate_themes(path: str = None) -> list[str]:
    """Validate the themes registry. Returns list of error strings."""
    if path is None:
        path = Path(__file__).parent / "themes.json"
    else:
        path = Path(path)

    errors = []

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return [f"File not found: {path}"]

    if "version" not in data:
        errors.append("Missing top-level 'version' field")
    if "themes" not in data:
        errors.append("Missing 'themes' array")
        return errors
    if not isinstance(data["themes"], list):
        errors.append("'themes' must be an array")
        return errors

    seen_ids = set()
    for i, theme in enumerate(data["themes"]):
        prefix = f"Theme [{i}] '{theme.get('id', '?')}'"

        if not isinstance(theme, dict):
            errors.append(f"Theme [{i}]: must be an object")
            continue

        # Required fields
        if "id" not in theme:
            errors.append(f"{prefix}: missing 'id'")
        elif theme["id"] in seen_ids:
            errors.append(f"{prefix}: duplicate theme ID")
        else:
            seen_ids.add(theme["id"])

        if "name" not in theme:
            errors.append(f"{prefix}: missing 'name'")

        # Validate CSS custom properties in light/dark
        for mode in ("light", "dark"):
            if mode not in theme:
                continue
            if not isinstance(theme[mode], dict):
                errors.append(f"{prefix}: '{mode}' must be an object")
                continue
            for prop_name, prop_value in theme[mode].items():
                if not CSS_PROP_NAME_RE.match(prop_name):
                    errors.append(f"{prefix}: {mode} property name '{prop_name}' must match --[a-z][-a-z]+")
                if not isinstance(prop_value, str):
                    errors.append(f"{prefix}: {mode} property '{prop_name}' value must be a string")
                elif CSS_FORBIDDEN_VALUES.search(prop_value):
                    errors.append(f"{prefix}: {mode} property '{prop_name}' contains forbidden value pattern (url(), expression(), javascript:, @import)")
                elif XSS_FORBIDDEN.search(prop_value):
                    errors.append(f"{prefix}: {mode} property '{prop_name}' contains XSS pattern")

        # Validate layout
        if "layout" in theme:
            layout = theme["layout"]
            if not isinstance(layout, dict):
                errors.append(f"{prefix}: 'layout' must be an object")
            else:
                if "sidebarOrder" in layout:
                    order = layout["sidebarOrder"]
                    if not isinstance(order, list):
                        errors.append(f"{prefix}: layout.sidebarOrder must be an array")
                    else:
                        for val in order:
                            if val not in VALID_SIDEBAR_PANELS:
                                errors.append(f"{prefix}: layout.sidebarOrder contains invalid panel '{val}' (allowed: {VALID_SIDEBAR_PANELS})")

        # Validate custom CSS field
        if "css" in theme:
            css = theme["css"]
            if not isinstance(css, str):
                errors.append(f"{prefix}: 'css' must be a string")
            elif len(css) > 50000:
                errors.append(f"{prefix}: css exceeds 50,000 characters")
            else:
                if CSS_FORBIDDEN_VALUES.search(css):
                    errors.append(f"{prefix}: css contains forbidden pattern (url(), expression(), javascript:, @import)")
                if XSS_FORBIDDEN.search(css):
                    errors.append(f"{prefix}: css contains XSS pattern")

    return errors


def validate_templates(path: str = None) -> list[str]:
    """Validate the templates registry. Returns list of error strings."""
    if path is None:
        path = Path(__file__).parent / "templates.json"
    else:
        path = Path(path)

    errors = []

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return [f"File not found: {path}"]

    if "version" not in data:
        errors.append("Missing top-level 'version' field")

    # Validate system prompts
    if "systemPrompts" in data:
        if not isinstance(data["systemPrompts"], list):
            errors.append("'systemPrompts' must be an array")
        else:
            seen_ids = set()
            for i, prompt in enumerate(data["systemPrompts"]):
                prefix = f"SystemPrompt [{i}] '{prompt.get('id', '?')}'"
                if not isinstance(prompt, dict):
                    errors.append(f"SystemPrompt [{i}]: must be an object")
                    continue
                if "id" not in prompt:
                    errors.append(f"{prefix}: missing 'id'")
                elif prompt["id"] in seen_ids:
                    errors.append(f"{prefix}: duplicate prompt ID")
                else:
                    seen_ids.add(prompt["id"])
                if "name" not in prompt:
                    errors.append(f"{prefix}: missing 'name'")
                if "prompt" not in prompt:
                    errors.append(f"{prefix}: missing 'prompt'")
                elif len(prompt["prompt"]) > 10000:
                    errors.append(f"{prefix}: prompt exceeds 10,000 characters")
                # XSS check on all string fields
                for field in ("name", "prompt", "category", "icon"):
                    val = prompt.get(field, "")
                    if isinstance(val, str) and XSS_FORBIDDEN.search(val):
                        errors.append(f"{prefix}: field '{field}' contains XSS pattern")

    # Validate prompt categories
    if "promptCategories" in data:
        if not isinstance(data["promptCategories"], list):
            errors.append("'promptCategories' must be an array")
        else:
            for i, cat in enumerate(data["promptCategories"]):
                if not isinstance(cat, dict):
                    errors.append(f"PromptCategory [{i}]: must be an object")
                    continue
                if "id" not in cat:
                    errors.append(f"PromptCategory [{i}]: missing 'id'")
                if "label" not in cat:
                    errors.append(f"PromptCategory [{i}]: missing 'label'")

    # Validate welcome screens
    if "welcomeScreens" in data:
        if not isinstance(data["welcomeScreens"], list):
            errors.append("'welcomeScreens' must be an array")
        else:
            seen_ids = set()
            for i, screen in enumerate(data["welcomeScreens"]):
                prefix = f"WelcomeScreen [{i}] '{screen.get('id', '?')}'"
                if not isinstance(screen, dict):
                    errors.append(f"WelcomeScreen [{i}]: must be an object")
                    continue
                if "id" not in screen:
                    errors.append(f"{prefix}: missing 'id'")
                elif screen["id"] in seen_ids:
                    errors.append(f"{prefix}: duplicate screen ID")
                else:
                    seen_ids.add(screen["id"])
                if "heading" not in screen:
                    errors.append(f"{prefix}: missing 'heading'")
                # XSS checks
                for field in ("heading", "subtitle", "name"):
                    val = screen.get(field)
                    if isinstance(val, str) and XSS_FORBIDDEN.search(val):
                        errors.append(f"{prefix}: field '{field}' contains XSS pattern")
                # Validate cards
                if "cards" in screen:
                    if not isinstance(screen["cards"], list):
                        errors.append(f"{prefix}: 'cards' must be an array")
                    else:
                        for j, card in enumerate(screen["cards"]):
                            card_prefix = f"{prefix} card [{j}]"
                            if not isinstance(card, dict):
                                errors.append(f"{card_prefix}: must be an object")
                                continue
                            if "action" in card and card["action"] and card["action"] not in VALID_WELCOME_ACTIONS:
                                errors.append(f"{card_prefix}: invalid action '{card['action']}' (allowed: {VALID_WELCOME_ACTIONS})")
                            for field in ("title", "description", "icon"):
                                val = card.get(field, "")
                                if isinstance(val, str) and XSS_FORBIDDEN.search(val):
                                    errors.append(f"{card_prefix}: field '{field}' contains XSS pattern")

    return errors


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    exit_code = 0

    if cmd == "packages":
        pkg_path = sys.argv[2] if len(sys.argv) > 2 else None
        errors = validate_packages(pkg_path)
        if errors:
            print(f"PACKAGES FAILED — {len(errors)} error(s):")
            for e in errors:
                print(f"  - {e}")
            exit_code = 1
        else:
            data = json.loads((Path(pkg_path) if pkg_path else Path(__file__).parent / "packages.json").read_text())
            print(f"PACKAGES OK — {len(data['packages'])} packages validated")

    elif cmd == "themes":
        theme_path = sys.argv[2] if len(sys.argv) > 2 else None
        errors = validate_themes(theme_path)
        if errors:
            print(f"THEMES FAILED — {len(errors)} error(s):")
            for e in errors:
                print(f"  - {e}")
            exit_code = 1
        else:
            data = json.loads((Path(theme_path) if theme_path else Path(__file__).parent / "themes.json").read_text())
            print(f"THEMES OK — {len(data['themes'])} themes validated")

    elif cmd == "templates":
        tpl_path = sys.argv[2] if len(sys.argv) > 2 else None
        errors = validate_templates(tpl_path)
        if errors:
            print(f"TEMPLATES FAILED — {len(errors)} error(s):")
            for e in errors:
                print(f"  - {e}")
            exit_code = 1
        else:
            data = json.loads((Path(tpl_path) if tpl_path else Path(__file__).parent / "templates.json").read_text())
            prompts = len(data.get('systemPrompts', []))
            screens = len(data.get('welcomeScreens', []))
            print(f"TEMPLATES OK — {prompts} prompts, {screens} welcome screens validated")

    elif cmd == "manifest":
        if len(sys.argv) < 3:
            print("Usage: validate.py manifest <path>")
            sys.exit(1)
        manifest_path = Path(sys.argv[2])
        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"MANIFEST FAILED — {e}")
            sys.exit(1)
        errors = validate_manifest(manifest)
        if errors:
            print(f"MANIFEST FAILED — {len(errors)} error(s):")
            for e in errors:
                print(f"  - {e}")
            exit_code = 1
        else:
            print(f"MANIFEST OK — '{manifest.get('name')}' v{manifest.get('version')} ({manifest.get('type', 'plugin')})")

    else:
        # Default: validate models.json (backward compatible)
        path = cmd  # cmd is either a path or None
        errors = validate(path)
        if errors:
            print(f"MODELS FAILED — {len(errors)} error(s):")
            for e in errors:
                print(f"  - {e}")
            exit_code = 1
        else:
            data = json.loads((Path(path) if path else Path(__file__).parent / "models.json").read_text())
            print(f"MODELS OK — {len(data['models'])} models validated")

    sys.exit(exit_code)
