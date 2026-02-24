"""Module E — Litigation Readiness: deterministic engine.

Data type registry, risk flags, and gap analysis for AI-specific
and traditional enterprise data sources.
"""

from dataclasses import dataclass, field


# -- Categories ----------------------------------------------------------------

AI_CATEGORIES = [
    "training_data",
    "model_artifacts",
    "api_interactions",
    "safety_alignment",
    "development_records",
]

TRADITIONAL_CATEGORIES = [
    "email_messaging",
    "documents_fileshares",
    "databases_applications",
    "cloud_saas",
]

CATEGORIES = AI_CATEGORIES + TRADITIONAL_CATEGORIES

SCENARIO_TYPES = [
    "copyright_training_data",
    "harmful_output",
    "antitrust",
    "ip_theft",
    "regulatory_inquiry",
    "employment_discrimination_ai",
    "contract_dispute",
    "data_breach",
    "trade_secret",
]


# -- Dataclasses --------------------------------------------------------------

@dataclass
class DataType:
    id: str
    category: str
    name: str
    description: str
    typical_volume: str
    typical_format: str
    retention_policy: str       # user-defined or "undefined"
    custodian: str              # human/system custodian or "unassigned"
    legal_risk: str             # "high" | "medium" | "low"
    preservation_complexity: str  # "high" | "medium" | "low"
    notes: str = ""


@dataclass
class RiskFlag:
    data_type_id: str
    flag_type: str              # "no_retention_policy" | "no_custodian" | etc.
    severity: str               # "critical" | "high" | "medium"
    detail: str


@dataclass
class LegalHold:
    scenario: str
    scenario_type: str
    affected_data_types: list[str] = field(default_factory=list)
    hold_scope_summary: str = ""
    estimated_volume: str = ""
    custodians: list[str] = field(default_factory=list)
    preservation_actions: list[str] = field(default_factory=list)
    privilege_considerations: list[str] = field(default_factory=list)
    cross_border_flags: list[str] = field(default_factory=list)


# -- Default registries -------------------------------------------------------

DEFAULT_AI_DATA_TYPES = [
    # Training Data (5)
    DataType("training_web_scrape", "training_data", "Web scrape corpora",
             "Large-scale web crawl datasets used for pre-training",
             "100TB+", "Common Crawl, JSONL, parquet",
             "undefined", "unassigned", "high", "high"),
    DataType("training_licensed", "training_data", "Licensed datasets",
             "Commercially licensed training data with contractual obligations",
             "10-50TB", "Parquet, CSV, JSONL",
             "undefined", "unassigned", "high", "medium"),
    DataType("training_synthetic", "training_data", "Synthetic data",
             "Model-generated training data for augmentation",
             "1-10TB", "JSONL, parquet",
             "undefined", "unassigned", "medium", "low"),
    DataType("training_rlhf", "training_data", "RLHF / human feedback",
             "Human preference labels and reward model training data",
             "100GB-1TB", "JSONL, CSV",
             "undefined", "unassigned", "high", "high"),
    DataType("training_finetune", "training_data", "Fine-tuning datasets",
             "Task-specific datasets for model fine-tuning",
             "1-100GB", "JSONL, CSV, parquet",
             "undefined", "unassigned", "medium", "medium"),

    # Model Artifacts (4)
    DataType("model_checkpoints", "model_artifacts", "Checkpoints / weights",
             "Serialized model parameters at training milestones",
             "10-500GB per checkpoint", "PyTorch .pt, SafeTensors, GGUF",
             "undefined", "unassigned", "high", "high"),
    DataType("model_configs", "model_artifacts", "Training configurations",
             "Hyperparameters, architecture specs, training scripts",
             "10-100MB", "YAML, JSON, Python",
             "undefined", "unassigned", "medium", "low"),
    DataType("model_evals", "model_artifacts", "Evaluation benchmarks",
             "Benchmark results, eval datasets, performance metrics",
             "1-10GB", "JSON, CSV, parquet",
             "undefined", "unassigned", "medium", "medium"),
    DataType("model_cards", "model_artifacts", "Model cards",
             "Documentation of model capabilities, limitations, intended use",
             "1-10MB", "Markdown, PDF",
             "undefined", "unassigned", "medium", "low"),

    # API Interactions (4)
    DataType("api_prompt_logs", "api_interactions", "Prompt / response logs",
             "Full request-response pairs from API endpoints",
             "10TB+/month", "JSONL, database records",
             "undefined", "unassigned", "high", "high"),
    DataType("api_system_prompts", "api_interactions", "System prompts",
             "System-level instructions configured by customers",
             "1-10GB", "JSON, database records",
             "undefined", "unassigned", "high", "medium"),
    DataType("api_tool_use", "api_interactions", "Tool use logs",
             "Function calling and tool invocation records",
             "1-5TB/month", "JSONL, database records",
             "undefined", "unassigned", "medium", "medium"),
    DataType("api_abuse_logs", "api_interactions", "Abuse detection logs",
             "Flagged content, policy violations, moderation decisions",
             "100GB-1TB/month", "JSONL, database records",
             "undefined", "unassigned", "high", "medium"),

    # Safety & Alignment (4)
    DataType("safety_evals", "safety_alignment", "Constitutional AI evals",
             "Safety evaluation results and constitutional AI training data",
             "10-100GB", "JSONL, CSV",
             "undefined", "unassigned", "high", "high"),
    DataType("safety_redteam", "safety_alignment", "Red team results",
             "Adversarial testing logs and vulnerability assessments",
             "1-10GB", "JSONL, Markdown, PDF",
             "undefined", "unassigned", "high", "high"),
    DataType("safety_incidents", "safety_alignment", "Safety incident reports",
             "Documented safety failures and remediation actions",
             "100MB-1GB", "PDF, Markdown, JSON",
             "undefined", "unassigned", "high", "medium"),
    DataType("safety_content_policy", "safety_alignment", "Content policy logs",
             "Content filtering decisions, policy update history",
             "1-5TB/month", "JSONL, database records",
             "undefined", "unassigned", "medium", "medium"),

    # Development Records (3)
    DataType("dev_experiment_tracking", "development_records", "Experiment tracking",
             "W&B, MLflow, or similar experiment metadata and metrics",
             "100GB-1TB", "Database, JSON, parquet",
             "undefined", "unassigned", "medium", "medium"),
    DataType("dev_code_repos", "development_records", "Code repository history",
             "Git history, PRs, code reviews for model development",
             "10-100GB", "Git objects, Markdown",
             "undefined", "unassigned", "medium", "low"),
    DataType("dev_internal_comms", "development_records", "Internal communications",
             "Slack, email, docs related to model development decisions",
             "Varies", "EML, JSON, database records",
             "undefined", "unassigned", "high", "medium"),
]

DEFAULT_TRADITIONAL_DATA_TYPES = [
    # Email & Messaging (3)
    DataType("email_exchange", "email_messaging", "Exchange Online / on-prem",
             "Microsoft Exchange email including calendar and contacts",
             "50GB per custodian", "PST, EML, MSG",
             "undefined", "unassigned", "high", "medium"),
    DataType("email_slack_teams", "email_messaging", "Slack / Teams messages",
             "Enterprise messaging platform communications",
             "10-50GB per workspace", "JSON, MHTML, database exports",
             "undefined", "unassigned", "high", "medium"),
    DataType("email_sms", "email_messaging", "SMS / mobile messaging",
             "Text messages, iMessage, WhatsApp business communications",
             "1-5GB per custodian", "XML, database, proprietary formats",
             "undefined", "unassigned", "high", "high"),

    # Documents & File Shares (3)
    DataType("docs_sharepoint", "documents_fileshares", "SharePoint / OneDrive",
             "Cloud document storage and collaboration platform",
             "100GB-1TB per site", "Office formats, PDF, media",
             "undefined", "unassigned", "medium", "medium"),
    DataType("docs_network_shares", "documents_fileshares", "Network file shares",
             "On-premises file servers and NAS storage",
             "1-50TB", "Mixed formats",
             "undefined", "unassigned", "medium", "medium"),
    DataType("docs_local", "documents_fileshares", "Local workstations",
             "End-user devices including laptops and desktops",
             "100GB-1TB per device", "Mixed formats",
             "undefined", "unassigned", "medium", "high"),

    # Databases & Applications (2)
    DataType("db_erp_crm", "databases_applications", "ERP / CRM systems",
             "Salesforce, SAP, Oracle business applications",
             "10-500GB", "Database, CSV, API exports",
             "undefined", "unassigned", "medium", "high"),
    DataType("db_hr_systems", "databases_applications", "HR systems",
             "Workday, ADP, BambooHR employee records",
             "1-10GB", "Database, CSV, PDF",
             "undefined", "unassigned", "high", "medium"),

    # Cloud & SaaS (2)
    DataType("cloud_google", "cloud_saas", "Google Workspace",
             "Gmail, Drive, Docs, Sheets, and related services",
             "50GB per custodian", "MBOX, Google formats, PDF",
             "undefined", "unassigned", "high", "medium"),
    DataType("cloud_collaboration", "cloud_saas", "Confluence / Jira",
             "Project management and knowledge base platforms",
             "10-100GB", "HTML, XML, database exports",
             "undefined", "unassigned", "medium", "medium"),
]

ALL_DEFAULT_DATA_TYPES = DEFAULT_AI_DATA_TYPES + DEFAULT_TRADITIONAL_DATA_TYPES


# -- Risk flag computation -----------------------------------------------------

def compute_risk_flags(data_types: list[DataType]) -> list[RiskFlag]:
    """Compute deterministic risk flags for a list of data types."""
    flags = []
    for dt in data_types:
        no_retention = not dt.retention_policy or dt.retention_policy.lower() in (
            "undefined", "")
        no_custodian = not dt.custodian or dt.custodian.lower() in (
            "unassigned", "")
        is_high_risk = dt.legal_risk == "high"

        if no_retention and no_custodian and is_high_risk:
            flags.append(RiskFlag(
                dt.id, "high_risk_unprotected", "critical",
                f"'{dt.name}' is high-risk with no retention policy and no custodian"))
        else:
            if no_retention:
                severity = "critical" if is_high_risk else "high"
                flags.append(RiskFlag(
                    dt.id, "no_retention_policy", severity,
                    f"'{dt.name}' has no retention policy defined"))
            if no_custodian:
                severity = "critical" if is_high_risk else "high"
                flags.append(RiskFlag(
                    dt.id, "no_custodian", severity,
                    f"'{dt.name}' has no custodian assigned"))

        if (dt.preservation_complexity == "high" and no_retention):
            # Only add if not already flagged as high_risk_unprotected
            if not (no_retention and no_custodian and is_high_risk):
                flags.append(RiskFlag(
                    dt.id, "complex_no_plan", "high",
                    f"'{dt.name}' has high preservation complexity but no retention policy"))

    return flags


# -- Gap analysis --------------------------------------------------------------

def _readiness_score(total: int, no_retention: int, no_custodian: int,
                     high_risk_total: int, high_risk_exposed: int) -> int:
    """Compute readiness score 0-100.

    40% retention coverage + 30% custodian coverage + 30% high-risk protection.
    """
    if total == 0:
        return 0
    retention_pct = (total - no_retention) / total
    custodian_pct = (total - no_custodian) / total
    if high_risk_total > 0:
        hr_protected_pct = (high_risk_total - high_risk_exposed) / high_risk_total
    else:
        hr_protected_pct = 1.0
    score = (retention_pct * 40) + (custodian_pct * 30) + (hr_protected_pct * 30)
    return round(score)


def compute_gap_analysis(data_types: list[DataType]) -> dict:
    """Return gap analysis summary for the data map."""
    total = len(data_types)
    no_retention = sum(
        1 for dt in data_types
        if not dt.retention_policy or dt.retention_policy.lower() in ("undefined", ""))
    no_custodian = sum(
        1 for dt in data_types
        if not dt.custodian or dt.custodian.lower() in ("unassigned", ""))
    high_risk = [dt for dt in data_types if dt.legal_risk == "high"]
    high_risk_total = len(high_risk)
    high_risk_exposed = sum(
        1 for dt in high_risk
        if (not dt.retention_policy or dt.retention_policy.lower() in ("undefined", ""))
        and (not dt.custodian or dt.custodian.lower() in ("unassigned", "")))

    present_categories = {dt.category for dt in data_types}
    missing_categories = [c for c in CATEGORIES if c not in present_categories]
    coverage_pct = round((len(present_categories) / len(CATEGORIES)) * 100, 1) if CATEGORIES else 0

    return {
        "total_data_types": total,
        "no_retention_policy": no_retention,
        "no_custodian": no_custodian,
        "high_risk_total": high_risk_total,
        "high_risk_exposed": high_risk_exposed,
        "missing_categories": missing_categories,
        "coverage_pct": coverage_pct,
        "readiness_score": _readiness_score(
            total, no_retention, no_custodian,
            high_risk_total, high_risk_exposed),
    }
