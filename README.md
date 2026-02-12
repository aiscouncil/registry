# AI Supreme Council — Community Registry

Community-managed model and package registries for [AI Supreme Council](https://aiscouncil.com).

## Registries

| File | Purpose | Entries |
|------|---------|--------|
| [`models.json`](models.json) | LLM model registry (providers, models, pricing, capabilities) | 50 models, 6 providers |
| [`packages.json`](packages.json) | Package registry (plugins, addons, mini-programs) | Community submissions |
| [`manifest-schema.json`](manifest-schema.json) | JSON Schema for manifest v2 validation | — |

## How It Works

The app fetches these registries on page load (24h cache). New models and packages appear automatically — no app update required.

**Fetch order:**
1. Same-origin `registry/*.json` (for self-hosted deployments)
2. `raw.githubusercontent.com/aiscouncil/registry/main/*.json` (CDN fallback)

## Models

6 providers, 50 models across free and paid tiers:

| Provider | Direct API Models | Via OpenRouter |
|----------|------------------|----------------|
| **Anthropic** | Claude Sonnet 4, Opus 4, Haiku 4.5 | + Opus 4.6, Opus 4.5, Sonnet 4.5 |
| **OpenAI** | GPT-4o, GPT-4o Mini, o3, o3 Mini, o1 | + via OR |
| **xAI** | Grok 3, Grok 3 Mini, Grok 3 Fast | + Grok 4, 4 Fast, 4.1 Fast |
| **Google Gemini** | Gemini 2.5 Flash/Pro/Flash-Lite (free) | + Gemini 3 Pro/Flash Preview |
| **OpenRouter** | 20+ free models (DeepSeek R1, Qwen 3, Llama 3.3, GPT-OSS, etc.) | Paid models from all providers |
| **Ollama** | Auto-detected local models | — |

## Packages

Four distribution tiers:

| Tier | Listing | Review | Badge |
|------|---------|--------|-------|
| **Direct Install** | Any manifest URL | None | None |
| **Community** | PR to `packages.json` | `validate.py` | Community |
| **AI Verified** | Community + paid AI scan | LLM audit | AI Verified |
| **Verified** | PR + manual review | Human review | Verified |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Adding models to the registry
- Publishing plugins, addons, and mini-programs
- Manifest v2 format and required fields
- Validation instructions

### Quick Start

```bash
# Add a model
# 1. Edit models.json, add your entry to the "models" array
# 2. Validate
python3 validate.py
# 3. Submit a PR

# Add a package
# 1. Edit packages.json, add your entry to the "packages" array
# 2. Validate
python3 validate.py packages
# 3. Submit a PR

# Validate a manifest file
python3 validate.py manifest path/to/manifest.json
```

## License

Registry data is open for community use. See [aiscouncil.com](https://aiscouncil.com) for platform terms.
