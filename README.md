# eDiscovery Toolkit

Local-first QC toolkit for eDiscovery professionals. Automates the highest-risk workflows for project managers, attorneys, and legal ops teams — production review, load file intake, and privilege log conformity — without sending client data to external services.

## Why

Manual QC of productions and load files is the highest-risk, most time-consuming task in eDiscovery project management. A single privileged document in an outgoing production can trigger sanctions, malpractice exposure, or case-altering consequences. This toolkit catches those issues before they leave the firm.

The architecture is a hybrid pipeline: deterministic structured parsing makes every pass/fail call, while a local LLM interprets unstructured inputs (ESI order PDFs) and generates human-readable reports. **The LLM never makes a QC determination.** The LLM integration layer is hardened with input sanitization, output schema validation, and prompt injection defense directives.

## Screenshots

**Upload and run QC checks:**

![Upload and run QC checks](docs/screenshots/module-b-upload.png)

**Results with privilege flags, issue breakdown chart, and export options:**

![QC results with privilege flags, Bates gaps, and cross-reference checks](docs/screenshots/module-b-results.png)

**LLM-generated counsel summary memo:**

![LLM-generated counsel summary memo](docs/screenshots/module-b-summary.png)

## Modules

### Intake QC

Validates incoming load files at receipt, before ingestion into the review platform. Catches formatting and completeness issues when redelivery is still cheap.

- Delimiter and encoding detection (UTF-8, Windows-1252)
- Required field presence and blank control numbers
- Duplicate control numbers and broken family ranges
- Purview ISO 8601 date format detection
- OPT image path cross-reference

### Search Term Workbench

LLM-assisted search term generation and QC for negotiation rounds. Extracts key concepts from case text, drafts dtSearch/Lucene terms with rationale, and provides analytics for iterative refinement.

- Two-stage LLM pipeline: concept extraction → term drafting
- Domain-specific term libraries (financial fraud, employment, IP theft)
- Deterministic name proximity variations — `first W/3 last` plus common nickname expansions (~45 mappings) for person entities, with automatic corporate name exclusion
- Custodian date range extraction and grouping (informational context for Relativity base search configuration)
- Syntax validation: unbalanced parentheses, missing proximity numbers, leading wildcards, lowercase boolean operators
- Risk flags: over-broad (>15% of dataset), subsumed (<5% unique ratio), attachment-heavy (family/doc ratio >3x)
- Per-term status workflow: draft → proposed → accepted / rejected / modified
- Excel export with round-based file naming for negotiation tracking

### Production QC

Final gate before documents leave the firm. Validates outgoing production metadata against ESI order specifications and flags privileged or PII-coded documents.

- Bates format, sequence, gaps, and duplicates
- Family integrity (parent produced implies all attachments produced)
- DAT to OPT cross-reference
- Privilege and PII coding flags
- Confidentiality designation validity
- LLM-generated counsel summary memo

### Privilege Log QC

Validates a privilege log draft against court-ordered specifications. Format and required field conformity only — no description generation (that carries liability risk outside the tool's scope).

- Required columns present per order spec
- Required fields populated (date, author, recipients, doc type, privilege basis)
- Privilege basis codes valid (ACP, WP, common interest, etc.)
- Format matches order (column order, headers, date format)

## Security Hardening

The LLM integration layer includes three defense layers to prevent prompt injection from manipulating which QC checks the deterministic engine runs:

**Input Sanitization** — All user-supplied text (PDF extracts, case descriptions) is scanned for injection patterns before reaching the LLM. Detected patterns are neutralized while preserving legitimate document content:
- Directive-like line starters (`System:`, `Instruction:`, `Prompt:`)
- XML/HTML role tags (`<system>`, `<instruction>`)
- "Ignore previous instructions" phrases
- Delimiter floods (5+ consecutive `#`, `=`, `-`)

**Output Schema Validation** — Every LLM JSON response is validated against a typed schema (required keys, type checks, enum constraints, list item types). Malformed responses are annotated with `_schema_errors` for review rather than silently accepted. Schemas cover all 5 JSON-returning prompts: ESI order extraction, privilege log spec, term concepts, term drafts, and field mapping.

**System Prompt Defense Directives** — All 6 LLM prompts include an identical directive block instructing the model to treat user content as data only and ignore embedded instructions, commands, or role overrides.

## Architecture

```
Streamlit UI
      |
Orchestration layer
      |
  ----+--------+-----------+------
  |            |           |      |
Intake QC  Search Terms  Prod QC  Priv Log QC
               |
         Name proximity        <-- deterministic nickname/W3 expansion
               |
Structured parsing engine      <-- all pass/fail decisions here
      |
LLM integration layer         <-- concept extraction, term drafting, reporting
```

## Supported File Formats

| Format | Use | Notes |
|--------|-----|-------|
| `.DAT` | Metadata load files | Concordance delimiters: `¶` (ASCII 020) field, `þ` (ASCII 254) qualifier |
| `.OPT` | Image load files | Standard comma-delimited |
| `.CSV` | Generic exports, Purview output | UTF-8 or Windows-1252 |
| `.PDF` | ESI orders, privilege log orders | Text extraction via pdfplumber, LLM interpretation |
| `.XLSX` | Privilege logs | openpyxl |

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally (for LLM features — QC checks work without it)

Minimum model: 8B (Llama 3.1 8B, Phi-4). Recommended: 32B+ for reliable legal document parsing.

## Setup

```bash
git clone https://github.com/m1chaeljonathan/ediscovery-toolkit.git
cd ediscovery-toolkit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure the LLM endpoint in `config.yaml`:

```yaml
llm:
  base_url: http://localhost:11434/v1
  model: llama3.1:8b          # or any Ollama model
  api_key: local
```

Start Ollama and pull a model:

```bash
ollama pull llama3.1:8b
```

## Usage

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Upload files in each tab, run QC checks, and export results as JSON, CSV, or XLSX.

## Running Tests

```bash
pytest tests/ -v
```

106 tests covering parser edge cases, all validators, search term analytics, name proximity generation, input sanitization, schema validation, LLM client hardening, and end-to-end module QC with synthetic fixtures.

## Project Structure

```
ediscovery-toolkit/
  app.py                    # Streamlit entry point
  config.yaml               # LLM endpoint, paths, limits
  parsers/
    dat_parser.py           # Concordance DAT parser
    opt_parser.py           # OPT image load file parser
    csv_parser.py           # Generic CSV / Purview parser
    schema.py               # Canonical Document dataclass
  modules/
    production_qc.py        # Production QC pipeline
    intake_qc.py            # Intake QC pipeline
    privilege_log_qc.py     # Privilege Log QC pipeline
    term_analytics.py       # Search term stats, syntax validation, risk flags
    validators/
      bates.py              # Bates sequence and format validation
      family.py             # Family integrity checks
      coding.py             # Privilege and PII coding flags
      crossref.py           # DAT/OPT cross-reference
    term_generator/
      generator.py          # Two-stage LLM pipeline (concepts → terms)
      name_proximity.py     # Deterministic name W/3 expansion + nicknames
      libraries/            # Domain-specific term libraries (JSON)
  llm/
    client.py               # OpenAI-compatible LLM abstraction (sanitize + schema)
    sanitize.py             # Input sanitization — prompt injection defense
    schemas.py              # Output schema definitions + validation
    esi_parser.py           # ESI order and privilege log spec extraction
    prompts/                # Versioned prompt templates (with defense directives)
  ui/
    module_a.py             # Intake QC tab
    module_b.py             # Production QC tab
    module_c.py             # Privilege Log QC tab
    module_d.py             # Search Term Workbench tab
  tests/
    fixtures/               # Synthetic DAT/OPT/CSV test data
```

## LLM Compatibility

The LLM client uses the OpenAI-compatible REST interface. Any of the following work — update `config.yaml` only:

| Runtime | Base URL |
|---------|----------|
| Ollama (default) | `http://localhost:11434/v1` |
| LM Studio | `http://localhost:1234/v1` |
| OpenAI API | `https://api.openai.com/v1` |
| Any OpenAI-compatible endpoint | per provider docs |

## Contributing

Contributions welcome. Please open an issue first to discuss what you'd like to change.

## License

[Apache License 2.0](LICENSE)
