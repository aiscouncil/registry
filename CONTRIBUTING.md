# Contributing to the Registries

AI Supreme Council maintains two community registries:

- **`registry/models.json`** — LLM model registry (providers + models)
- **`registry/packages.json`** — Package registry (plugins, addons, mini-programs)

Both are community-managed via pull requests. Changes take effect on next user page load (24h cache).

---

## Model Registry

### Adding a Model

1. Fork this repository
2. Edit `registry/models.json`
3. Add your model entry to the `models` array
4. Run validation: `python3 registry/validate.py`
5. Submit a PR

### Model Entry Format

```json
{
  "id": "provider-org/model-name:free",
  "name": "Human Readable Name (Free)",
  "provider": "openrouter",
  "context": 128000,
  "maxOutput": 8192,
  "pricing": { "input": 0, "output": 0 },
  "capabilities": ["tools", "streaming"],
  "tier": "free"
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique model identifier (must match the API's model ID) |
| `name` | string | Human-readable display name |
| `provider` | string | Provider key: `anthropic`, `openai`, `xai`, `gemini`, `openrouter`, `ollama` |
| `context` | number | Context window size in tokens (must be > 0) |
| `maxOutput` | number | Maximum output tokens (must be > 0) |
| `pricing` | object | `{ "input": number, "output": number }` — cost per 1M tokens (0 for free) |
| `capabilities` | array | Subset of: `vision`, `tools`, `streaming`, `json_mode`, `reasoning` |
| `tier` | string | One of: `free`, `paid`, `enterprise` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `default` | boolean | Mark as default model for this provider |
| `reasoning` | boolean | Model supports chain-of-thought reasoning |
| `rateLimit` | string | Human-readable rate limit info (e.g., "10 RPM free tier") |

### Adding a New Provider

Add to the `providers` object:

```json
"my-provider": {
  "name": "My Provider",
  "baseUrl": "https://api.example.com/v1/chat/completions",
  "authType": "bearer",
  "keyUrl": "https://example.com/keys",
  "format": "openai"
}
```

Required provider fields: `name`, `baseUrl`, `authType`, `format`.

- `authType`: `bearer` (Authorization header), `header` (custom header via `authHeader`), `query` (URL parameter via `authParam`), `none`
- `format`: `openai` (OpenAI-compatible SSE), `anthropic` (Anthropic SSE), `gemini` (Google Gemini API)

---

## Package Registry

The package registry lists plugins, addons, and mini-programs for the aiscouncil platform.

### Extension Types

| Type | Sandbox | UI Surface | Use Case |
|------|---------|-----------|----------|
| **Plugin** | WASM (kernel slots 4-7) | None — hooks only | Filters, translators, analytics |
| **Addon** | WASM or JS | Named UI slots | Dashboards, settings panels |
| **Mini-Program** | Sandboxed iframe | Replaces chat area | Code editors, kanban, AI art, games |

### Marketplace Tiers

| Tier | How to List | Review | Trust Badge | Paid Apps |
|------|-------------|--------|------------|-----------|
| **Direct Install** | User pastes any manifest URL | None | None | No |
| **Community** | PR to `registry/packages.json` | Automated (`validate.py`) | Community | Yes |
| **AI Verified** | Community + paid AI scan | LLM security audit | AI Verified | Yes |
| **Verified** | PR + manual team review | Human review | Verified | Yes |

**Direct Install** requires no registry listing. Users install by calling `AIS.MiniPrograms.install(manifestUrl)` with any URL. No review, no trust badge, free only.

**Community** packages are listed in the registry via PR. Auto-merged if `validate.py` passes. Developers can set a price (optional). Community packages show a "Community" badge.

**AI Verified** packages have passed an AI-powered security scan. Any Community package can earn this badge by submitting to the verification API. The AI checks for malware, data exfiltration, obfuscated code, permission misuse, and sandbox escape attempts. See [AI Verification](#ai-verification) below for details.

**Verified** packages undergo manual security and quality review. They receive a "Verified" badge and featured placement in the apps grid. Request verification by adding `"tier": "verified"` in your PR — a maintainer will review.

### Publishing a Free Package

1. Create your manifest file (see [Manifest v2 Format](#manifest-v2-format) below)
2. Host your files on any CDN/server (GitHub Pages, Cloudflare Pages, Vercel, etc.)
3. Fork this repository
4. Add an entry to `registry/packages.json`:

```json
{
  "name": "my-app",
  "type": "mini-program",
  "version": "1.0.0",
  "manifest": "https://cdn.example.com/my-app/manifest.json",
  "tier": "community",
  "description": "Short description of what it does",
  "icon": "https://cdn.example.com/my-app/icon.png",
  "added": "2026-02-10"
}
```

5. Run validation: `python3 registry/validate.py packages`
6. Submit a PR

### Publishing a Paid Package

Paid packages work the same as free, but with pricing fields:

```json
{
  "name": "pro-editor",
  "type": "mini-program",
  "version": "2.0.0",
  "manifest": "https://cdn.example.com/pro-editor/manifest.json",
  "tier": "community",
  "price": 499,
  "currency": "USD",
  "seller": {
    "name": "DevCo",
    "id": "seller_abc123"
  },
  "description": "Professional code editor with AI assist",
  "icon": "https://cdn.example.com/pro-editor/icon.png",
  "added": "2026-02-10"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `price` | For paid | Price in cents (e.g., `499` = $4.99). `0` or absent = free |
| `currency` | For paid | ISO 4217 code (default: `USD`) |
| `seller` | For paid | `{ "name": "Display Name", "id": "seller_xxx" }` — Stripe Connect account ID |

**Commission:** The platform takes 15% of each sale. Sellers receive 85% via Stripe Connect payouts.

**Becoming a seller:** Before listing a paid app, you must connect your Stripe account via the Settings > Account > Developer section (coming soon). Your `seller.id` is your Stripe Connect account ID.

### Package Entry Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | string | Package name (must match manifest `name`) |
| `type` | Yes | string | `plugin`, `addon`, or `mini-program` |
| `version` | Yes | string | Semver version (must match manifest `version`) |
| `manifest` | Yes | string | URL to the hosted `manifest.json` |
| `tier` | No | string | `community` (default), `ai-verified`, or `verified` |
| `description` | No | string | Short description for the store listing |
| `icon` | No | string | URL to icon (128x128 PNG recommended) |
| `added` | No | string | ISO 8601 date when first listed |
| `price` | No | number | Price in cents (0 or absent = free) |
| `currency` | No | string | ISO 4217 currency code (default: USD) |
| `seller` | For paid | object | `{ "name": string, "id": string }` |
| `verification` | For ai-verified | object | `{ "hash": string, "tier": string, "date": string, "expires": string, "job_id": string }` |

### Manifest v2 Format

Every package needs a `manifest.json` hosted at a public URL. The manifest uses the [manifest v2 schema](manifest-schema.json).

**Mini-program manifest:**
```json
{
  "$schema": "https://aiscouncil.com/schema/manifest/v2",
  "name": "my-app",
  "version": "1.0.0",
  "abi": 1,
  "type": "mini-program",
  "description": "What this app does",
  "author": { "name": "Your Name", "url": "https://example.com" },
  "permissions": ["storage", "ui:toast"],
  "entry": "index.html",
  "base_url": "https://cdn.example.com/my-app/",
  "keywords": ["utility"]
}
```

**Plugin manifest:**
```json
{
  "$schema": "https://aiscouncil.com/schema/manifest/v2",
  "name": "my-plugin",
  "version": "1.0.0",
  "abi": 1,
  "type": "plugin",
  "description": "What this plugin does",
  "wasm": "https://cdn.example.com/my-plugin/plugin.wasm",
  "wasm_sha256": "a1b2c3d4e5f6...",
  "hooks": [
    { "name": "chat:before-send", "priority": 50 }
  ]
}
```

**Type-specific required fields:**

| Type | Required Fields |
|------|----------------|
| `plugin` | `wasm`, `wasm_sha256` |
| `addon` | `wasm` or `entry` |
| `mini-program` | `entry`, `base_url` |

### ABI Version

All manifests should include `"abi": 1`. This pins the package to ABI v1 (the current frozen API surface). The platform rejects manifests with unsupported ABI versions.

ABI v1 guarantees:
- 35 kernel WASM exports (including `kernel_abi_version`)
- 64 MB shared memory layout
- 8-export module ABI (`bcz_mount`, `bcz_resume`, `bcz_handle`, `bcz_tick`, `bcz_drain`, `bcz_version`, `bcz_seg_size`, `bcz_health`)
- Manifest v2 schema
- SDK postMessage bridge protocol (`window.ais` namespace)
- Additive changes only — new exports, new SDK methods, new hooks, new permissions never break existing packages

### Permissions

Mini-programs request permissions in their manifest. Users approve permissions at install time.

| Permission | Access |
|-----------|--------|
| `storage` | Per-app isolated key-value storage (always allowed) |
| `chat:read` | Read chat history |
| `chat:write` | Send messages |
| `config:read` | Read bot configuration |
| `config:write` | Modify bot configuration |
| `auth:read` | Read user info (name, email, picture, tier) |
| `ui:toast` | Show toast notifications |
| `ui:modal` | Show confirmation dialogs |
| `hooks:action` | Register and fire hook events |
| `hooks:filter` | Register filter hooks |
| `network:fetch` | Make proxied network requests (future) |

### Validate Before Submitting

```bash
# Validate models registry
python3 registry/validate.py

# Validate packages registry
python3 registry/validate.py packages

# Validate a single manifest file
python3 registry/validate.py manifest path/to/manifest.json
```

---

## AI Verification

Any Community-listed package can earn an **"AI Verified"** badge by passing an AI-powered security scan. This gives users confidence that the code has been analyzed for common threats.

### Scan Tiers

| Tier | Price | Code Size Limit | Turnaround | Badge Earned |
|------|-------|----------------|------------|-------------|
| **Quick Scan** | $19 | 100 KB | ~30 min | "AI Scanned" |
| **Full Audit** | $49 | 500 KB | ~2 hours | "AI Verified" |
| **Deep Audit** | $99 | 2 MB | ~24 hours | "AI Verified + Reviewed" |

### What Gets Checked

- **Malware patterns** — `eval()`, `Function()`, crypto miners, keyloggers
- **Data exfiltration** — `fetch()`/`XMLHttpRequest` to domains not in `base_url`, `navigator.sendBeacon()`
- **Obfuscated code** — Base64-encoded eval, char code assembly, hex variable names
- **Permission misuse** — Requesting permissions your code doesn't actually use (or using APIs you didn't request)
- **Sandbox escape** — Attempts to access `parent.document`, `window.top`, `localStorage` directly
- **Hardcoded secrets** — API keys, tokens, passwords in source code
- **Privacy violations** — Fingerprinting, tracking pixels, cookie access attempts

### How to Get Verified

1. **Publish your app** as a Community package first (submit a PR, get merged)
2. **Submit a verification request:**
   ```
   POST https://api.aiscouncil.com/v1/verify/submit
   {
     "manifest_url": "https://cdn.example.com/my-app/manifest.json",
     "scan_tier": "full"
   }
   ```
   (Requires authentication — use your JWT from the platform)
3. **Pay the scan fee** via the returned Stripe checkout link ($19/$49/$99)
4. **Wait for results** — check status via `GET /v1/verify/status/{job_id}`
5. **If passed**, add the `verification` object to your registry entry:
   ```json
   {
     "name": "my-app",
     "type": "mini-program",
     "version": "1.0.0",
     "manifest": "https://cdn.example.com/my-app/manifest.json",
     "tier": "community",
     "verification": {
       "hash": "a1b2c3d4e5f6...",
       "tier": "full",
       "date": "2026-02-10",
       "expires": "2027-02-10",
       "job_id": "ver_abc123"
     }
   }
   ```
6. **Submit a PR** with the updated entry. `validate.py` will confirm the badge is valid.

### Badge Rules

- Badge is tied to a **SHA-256 content hash** of your app's code. If you change even one byte and publish a new version, the badge is removed until you re-verify.
- Badge expires after **12 months**. Re-verify annually to maintain the badge.
- On install, the platform computes the hash of the fetched HTML and compares it against the badge hash. Mismatch = badge not displayed.
- **Failed scans** return a detailed report with findings and remediation guidance. Fix the issues and re-submit.

### Limits

- **Per developer:** 5 Quick / 3 Full / 1 Deep scans per month
- **Code size:** 100 KB (Quick), 500 KB (Full), 2 MB (Deep)
- **Re-scan cooldown:** 1 hour per manifest URL
- **Platform daily cap:** 50 scans/day (scales with demand)

---

## Fetch Locations

The app tries these URLs in order for each registry:

**Models:**
1. `registry/models.json` (same-origin, for self-hosted)
2. `https://raw.githubusercontent.com/aiscouncil/registry/main/registry/models.json` (GitHub fallback)

**Packages:**
1. `registry/packages.json` (same-origin)
2. `https://raw.githubusercontent.com/aiscouncil/registry/main/registry/packages.json` (GitHub fallback)

For faster CDN delivery, consider hosting on Cloudflare Pages or GitHub Pages which provides global edge caching.

## Rate of Updates

- Both registries are cached for 24 hours in the browser
- On each page load, the app fetches fresh data in the background
- If the `version` field changes, stale data is refreshed immediately
- Users see updated listings on their next page load after a PR is merged
