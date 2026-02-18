# AI Supreme Council — Community Registry

Community-managed registries and translations for [AI Supreme Council](https://aiscouncil.com).

## What's Here

| Path | Purpose |
|------|---------|
| [`models.json`](models.json) | LLM model registry — 50 models, 6 providers, pricing, capabilities |
| [`packages.json`](packages.json) | Package registry — plugins, addons, mini-programs |
| [`templates.json`](templates.json) | System prompt templates and welcome screens |
| [`themes.json`](themes.json) | Theme definitions (light/dark CSS custom properties) |
| [`design-tokens.json`](design-tokens.json) | Design token library |
| [`manifest-schema.json`](manifest-schema.json) | JSON Schema for manifest v2 validation |
| [`locale/`](locale/) | Translations (10 languages) |
| [`validate.py`](validate.py) | Validation script for all registries |

## Contributing Translations

We welcome translations from both humans and AI/LLM agents.

**Quick start:**
1. Copy [`locale/en.json`](locale/en.json) to `locale/{lang}.json`
2. Translate every value (not the keys)
3. Keep `{template}` variables exactly as-is
4. Validate: `python3 locale/validate_locale.py locale/{lang}.json`
5. Submit a PR

**Detailed guides:**
- [Translation Guide](locale/TRANSLATING.md) — rules, examples, character encoding
- [LLM Translation Task](locale/TRANSLATE_TASK.md) — structured instructions for AI agents

**Current translations:**

| Language | Code | Status |
|----------|------|--------|
| English | `en` | Source |
| Spanish | `es` | Complete |
| Chinese (Simplified) | `zh` | Complete |
| Arabic | `ar` | Complete |
| French | `fr` | Complete |
| Portuguese | `pt` | Complete |
| Japanese | `ja` | Complete |
| Korean | `ko` | Complete |
| German | `de` | Complete |
| Russian | `ru` | Complete |
| Hindi | `hi` | Needed |
| Turkish | `tr` | Needed |
| Ukrainian | `uk` | Needed |
| Thai | `th` | Needed |
| Polish | `pl` | Needed |
| Italian | `it` | Needed |
| Dutch | `nl` | Needed |
| Indonesian | `id` | Needed |
| Vietnamese | `vi` | Needed |

## Contributing Models & Packages

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Adding models to the registry
- Publishing plugins, addons, and mini-programs
- Manifest v2 format and validation

```bash
# Validate models
python3 validate.py

# Validate packages
python3 validate.py packages

# Validate themes
python3 validate.py themes

# Validate templates
python3 validate.py templates

# Validate all locale files
python3 locale/validate_locale.py --all
```

## How It Works

The app fetches these registries with a 24h stale-while-revalidate cache:

1. Same-origin `registry/*.json` (primary — bundled with deployment)
2. `raw.githubusercontent.com/aiscouncil/registry/main/*.json` (GitHub fallback)

New models, translations, and packages appear automatically — no app update required.

## CI

Every PR runs [GitHub Actions](.github/workflows/validate.yml) that validates all registries and locale files. PRs with validation errors cannot merge.

## License

Registry data is MIT licensed. Translations are community-contributed under CC0.
