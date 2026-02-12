#!/usr/bin/env python3
"""Validate registry/models.json and registry/packages.json for aiscouncil."""
import json
import re
import sys
from pathlib import Path

REQUIRED_MODEL_FIELDS = {"id", "name", "provider", "context", "maxOutput", "pricing", "capabilities", "tier"}
ALLOWED_CAPABILITIES = {"vision", "tools", "streaming", "json_mode", "reasoning"}
ALLOWED_TIERS = {"free", "paid", "enterprise"}
REQUIRED_PROVIDER_FIELDS = {"name", "baseUrl", "authType", "format"}

# Package registry constants
ALLOWED_PACKAGE_TYPES = {"plugin", "addon", "mini-program"}
ALLOWED_REGISTRY_TIERS = {"community", "ai-verified", "verified"}
ALLOWED_VERIFICATION_TIERS = {"quick", "full", "deep"}
HASH_RE = re.compile(r'^[0-9a-f]{64}$')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}')
JOB_ID_RE = re.compile(r'^ver_[a-zA-Z0-9]+$')
ALLOWED_PERMISSIONS = {
    "storage", "chat:read", "chat:write", "config:read", "config:write",
    "auth:read", "ui:toast", "ui:modal", "hooks:action", "hooks:filter", "network:fetch"
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
            # Paid apps need a seller
            if pkg.get("price", 0) > 0 and "seller" not in pkg:
                errors.append(f"{prefix}: paid packages require a 'seller' object")

        # Seller
        if "seller" in pkg:
            seller = pkg["seller"]
            if not isinstance(seller, dict):
                errors.append(f"{prefix}: seller must be an object")
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
