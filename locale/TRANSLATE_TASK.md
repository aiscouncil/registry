# Translation Task for AI/LLM Agents

## What You Need To Do

Translate the AI Supreme Council wizard UI into a target language.

## Steps

### 1. Read the source file
Read `locale/en.json` — this is the English source of truth.

### 2. Read the example
Read `locale/es.json` — this is a complete Spanish translation to use as a reference.

### 3. Create your translation
Create a new file `locale/{lang}.json` where `{lang}` is the ISO 639-1 language code.

**Copy the structure from `en.json` exactly.** Translate every value. Do NOT change any keys.

### 4. Update `_meta`
```json
"_meta": {
  "lang": "xx",        ← your ISO 639-1 code
  "name": "Language",   ← language name in that language
  "version": 1,         ← keep as 1
  "module": "wizard"    ← keep as "wizard"
}
```

### 5. Preserve template variables
Strings with `{curly braces}` contain variables. Keep them exactly:
- `{name}` → a person or provider name
- `{count}` → a number
- `{s}` → plural suffix
- `{min}` → minimum notice
- `{error}` → error message

Example: `"Operator: {name}"` → `"Opérateur : {name}"` (French)

### 6. Validate
```bash
python3 locale/validate_locale.py locale/xx.json
```
Must print `✓ xx.json — OK`.

### 7. Do NOT translate these
- `"appName"` value — keep as "AI SUPREME COUNCIL" (brand name)
- Model names (Claude, GPT, Gemini, etc.)
- Provider names (Anthropic, OpenAI, etc.)
- Technical terms: API, JSON, URL, endpoint, OpenAI
- The `_meta` object keys

## Target Languages (priority order)

| Code | Language | Status |
|------|----------|--------|
| `es` | Spanish | Done |
| `zh` | Chinese (Simplified) | Done |
| `ar` | Arabic | Done |
| `fr` | French | Done |
| `pt` | Portuguese | Done |
| `ja` | Japanese | Done |
| `ko` | Korean | Done |
| `de` | German | Done |
| `ru` | Russian | Done |
| `hi` | Hindi | Needed |
| `tr` | Turkish | Needed |
| `uk` | Ukrainian | Needed |
| `th` | Thai | Needed |
| `pl` | Polish | Needed |
| `it` | Italian | Needed |
| `nl` | Dutch | Needed |
| `id` | Indonesian | Needed |
| `vi` | Vietnamese | Needed |

## Tone Guidelines
- Military/tech aesthetic — concise, professional, operational
- Use imperative mood for buttons ("Create Profile", not "Click here to create a profile")
- Match the English tone — not casual, not overly formal

## File Location
All locale files go in: `locale/`
