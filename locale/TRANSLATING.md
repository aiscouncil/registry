# Translating AI Supreme Council

## Quick Start

1. Copy `en.json` to `{lang}.json` (e.g. `es.json`, `zh.json`, `ar.json`)
2. Translate every value (NOT the keys)
3. Update `_meta.lang` and `_meta.name`
4. Submit a PR

## Rules

### DO translate
- All string values (the right side of each `"key": "value"` pair)
- The `_meta.name` field (e.g. "Spanish", "Español")

### DO NOT change
- Any key names (the left side)
- The `_meta.lang` code (use ISO 639-1: `es`, `zh`, `ar`, `fr`, `de`, `ja`, `ko`, etc.)
- The `_meta.version` number (keep it matching `en.json`)
- The `_meta.module` field (keep as `"wizard"`)
- Template variables inside `{curly braces}` — these are replaced at runtime

### Template variables
Some strings contain `{variable}` placeholders. Keep them exactly as-is:

| Variable | Meaning | Example |
|----------|---------|---------|
| `{name}` | User's name or provider name | "Operator: {name}" → "Operador: {name}" |
| `{count}` | A number | "{count} selected:" → "{count} seleccionados:" |
| `{s}` | Plural suffix (empty or "s") | "model{s}" — keep `{s}` where it appears |
| `{min}` | Minimum notice text | Keep `{min}` in place |
| `{error}` | Error message | Keep `{error}` in place |

### Character encoding
- Use UTF-8 (JSON default)
- Unicode escapes like `\u2713` (✓) and `\u2192` (→) are fine to keep or replace with actual characters
- Keep `\u2014` (—) as-is or use the actual em-dash character

## Example: Spanish (es.json)

```json
{
  "_meta": {
    "lang": "es",
    "name": "Español",
    "version": 1,
    "module": "wizard"
  },
  "appName": "AI SUPREME COUNCIL",
  "createProfile": "Crear Perfil de IA",
  "operator": "Operador: {name}",
  "standard": "ESTÁNDAR",
  "singleModel": "Modelo Único",
  "singleDesc": "Despliega un modelo de IA. Configura proveedor, conecta credenciales, inicia operaciones.",
  ...
}
```

## Validation

After translating, verify:
1. Valid JSON: `python3 -c "import json; json.load(open('xx.json'))"`
2. Same keys as `en.json`: `python3 locale/validate_locale.py locale/xx.json`
3. No missing `{variables}`: the validation script checks this automatically

## Priority Languages

| Priority | Language | Code | Status |
|----------|----------|------|--------|
| 1 | English | `en` | Complete (source) |
| 2 | Spanish | `es` | Complete |
| 3 | Chinese (Simplified) | `zh` | Complete |
| 4 | Arabic | `ar` | Complete |
| 5 | French | `fr` | Complete |
| 6 | Portuguese | `pt` | Complete |
| 7 | Japanese | `ja` | Complete |
| 8 | Korean | `ko` | Complete |
| 9 | German | `de` | Complete |
| 10 | Russian | `ru` | Complete |
| 11 | Hindi | `hi` | Needed |
| 12 | Turkish | `tr` | Needed |
| 13 | Ukrainian | `uk` | Needed |
| 14 | Thai | `th` | Needed |
| 15 | Polish | `pl` | Needed |
| 16 | Italian | `it` | Needed |
| 17 | Dutch | `nl` | Needed |
| 18 | Indonesian | `id` | Needed |
| 19 | Vietnamese | `vi` | Needed |

## For LLM Translators

If you are an AI/LLM doing the translation:

1. Read `en.json` completely
2. Create a new file `{lang}.json` with the same structure
3. Translate naturally — don't be overly literal. Match the tone (military/tech aesthetic)
4. Keep `{variable}` placeholders exactly as they appear in English
5. Keep the `_meta` block updated with the correct `lang` and `name`
6. For RTL languages (Arabic, Hebrew): the app handles text direction via CSS; just translate the strings
7. Run the validation script to confirm all keys are present
8. Do NOT translate: model names, provider names, technical terms (API, JSON, URL)
