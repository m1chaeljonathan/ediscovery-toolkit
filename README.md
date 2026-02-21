# eDiscovery Toolkit

Local-first QC toolkit for eDiscovery professionals. Automates the highest-risk workflows for project managers, attorneys, and legal ops teams — production review, load file intake, and privilege log conformity — without sending client data to external services.

## Modules

### Module B — Production QC (priority 1)

Final gate before documents leave the firm. Validates outgoing production metadata against ESI order specifications and flags privileged or PII-coded documents before production.

Checks:
- Bates format, sequence, gaps, and duplicates
- Family integrity (parent produced implies all attachments produced)
- DAT to OPT cross-reference
- Privilege and PII coding flags
- Confidentiality designation validity

Output: `summary.md` for counsel, `flagged_docs.csv` for PM remediation, `stats.json`.

### Module A — Load file intake QC (priority 2)

Validates incoming load files at receipt, before ingestion into the review platform. Catches formatting and completeness issues when redelivery is still cheap.

Checks:
- Delimiter and encoding detection (UTF-8, Windows-1252)
- Required field presence and blank control numbers
- Duplicate control numbers and broken family ranges
- Purview ISO 8601 date format flag
- OPT image path cross-reference

Output: `summary.md`, `field_mapping.csv`, `issues.csv`, `redelivery_memo.md`.

### Module C — Privilege log conformity QC (priority 3)

Validates a privilege log draft against the court-ordered privilege log specifications. Format and required field conformity only — no description generation.

Checks:
- Required columns present per order spec
- Required fields populated (date, author, recipients, doc type, privilege basis)
- Privilege basis codes valid (ACP, WP, common interest, etc.)
- Format matches order (column order, headers, date format, sort order)

Output: `conformity_report.md`, `flagged_entries.csv`, `spec_summary.md`.

## Architecture

Two layers with a hard boundary between them:

```
Web UI (Streamlit)
        |
Orchestration layer
        |
  ------+------+------
  |            |     |
Module B  Module A  Module C
        |
Structured parsing engine   <-- all pass/fail decisions here
        |
LLM integration layer       <-- interpretation and report generation only
```

The structured parsing engine makes every pass/fail call. The LLM interprets unstructured inputs (ESI order PDFs, privilege log orders) and generates human-readable output. The LLM never makes a QC determination.

## Supported file formats

| Format | Use | Notes |
|--------|-----|-------|
| `.DAT` | Metadata load files | Concordance delimiters: `¶` (ASCII 020) field, `þ` (ASCII 254) qualifier |
| `.OPT` | Image load files | Standard comma-delimited |
| `.CSV` | Generic exports, Purview output | UTF-8 or Windows-1252 |
| `.PDF` | ESI orders, privilege log orders | LLM extraction via pdfplumber |
| `.XLSX` | Privilege logs | openpyxl |

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally with a supported model

Minimum model: Llama 3.1 8B. Recommended: 32B+ for reliable legal document parsing.

## Setup

1. Clone the repository

```bash
git clone ssh://git@192.168.50.66:2222/m1chaeljonathan/ediscovery-toolkit.git
cd ediscovery-toolkit
```

2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure the LLM endpoint in `config.yaml`

```yaml
llm:
  base_url: http://localhost:11434/v1
  model: llama3.1:32b
  api_key: local

server:
  upload_dir: ./uploads
  report_dir: ./reports/output
  max_file_size_mb: 500
```

4. Start Ollama and pull a model

```bash
ollama pull llama3.1:32b
```

## Running the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Upload files in each tab and run QC checks. Results display in-browser and export to the configured report directory.

## Running tests

```bash
pytest tests/ -v
```

Test fixtures are synthetic load files covering clean and issue scenarios. EDRM sample data (edrm.net) can be placed in `tests/fixtures/` for end-to-end validation.

## Project structure

```
ediscovery-toolkit/
  app.py                    # Streamlit entry point
  config.yaml               # LLM endpoint, paths, limits
  requirements.txt
  parser/
    dat_parser.py           # Concordance DAT parser
    opt_parser.py           # OPT image load file parser
    csv_parser.py           # Generic CSV / Purview parser
    schema.py               # Canonical Document dataclass
    validator.py
  modules/
    production_qc.py        # Module B pipeline
    intake_qc.py            # Module A pipeline
    privilege_log_qc.py     # Module C pipeline
    validators/
      bates.py
      family.py
      coding.py
      crossref.py
  llm/
    client.py               # OpenAI-compatible abstraction
    esi_parser.py           # ESI order and privilege log spec extraction
    prompts/                # Versioned prompt templates
  ui/
    module_a.py
    module_b.py
    module_c.py
  reports/
    output/                 # Generated QC reports
  tests/
    fixtures/               # Sample DAT/OPT files for testing
```

## LLM compatibility

The LLM client uses the OpenAI-compatible REST interface. Any of the following work without code changes — update `config.yaml` only:

| Runtime | Base URL |
|---------|----------|
| Ollama (default) | `http://localhost:11434/v1` |
| LM Studio | `http://localhost:1234/v1` |
| OpenAI | `https://api.openai.com/v1` |
| Anthropic (via proxy) | per proxy config |

## Test data sources

- [EDRM sample data](https://edrm.net/resources/data-sets/) — proper DAT/OPT with metadata, designed for eDiscovery tool testing
- Enron email corpus — widely recognized, useful for demo scenarios
- TREC Legal Track — benchmarking legal IR components

## Status

POC in active development. See `plans/2026-02-21-ediscovery-toolkit-poc.md` for the 22-task implementation plan.

## Related

- Design document: `plans/design.md`
- Vault notes: `02_ai_ml/projects/ediscovery-toolkit/`
