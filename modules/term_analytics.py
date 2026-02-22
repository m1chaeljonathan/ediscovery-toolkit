import re
from dataclasses import dataclass, field

OVER_BROAD_THRESHOLD = 0.15   # 15% of dataset
SUBSUMED_THRESHOLD   = 0.05   # <5% unique ratio
ATTACHMENT_THRESHOLD = 3.0    # family / doc ratio


@dataclass
class TermStats:
    term_text:         str
    syntax:            str
    doc_hits:          int     = 0
    family_hits:       int     = 0
    unique_hits:       int     = 0
    total_docs:        int     = 0
    pct_of_dataset:    float   = 0.0
    family_multiplier: float   = 0.0
    unique_ratio:      float   = 0.0
    risk_flags:        list[str] = field(default_factory=list)
    syntax_errors:     list[str] = field(default_factory=list)
    lucene_equivalent: str     = ""
    rationale:         str     = ""
    proposed_by:       str     = "pm"
    status:            str     = "draft"


def validate_syntax(term: str, syntax: str = 'dtsearch') -> list[str]:
    errors = []
    if not term:
        return errors
    if term.count('(') != term.count(')'):
        errors.append("Unbalanced parentheses")
    if re.search(r'\bW/(?!\d)', term):
        errors.append("W/ missing proximity number")
    if re.search(r'\bPRE/(?!\d)', term):
        errors.append("PRE/ missing proximity number")
    if re.search(r'(?<!\w)\*\w', term):
        errors.append("Leading wildcard — avoid in dtSearch")
    if syntax == 'dtsearch' and re.search(r'\b(and|or|not)\b', term):
        errors.append("Boolean operators must be uppercase (AND/OR/NOT)")
    return errors


def compute_stats(terms: list[dict], total_docs: int,
                  threshold: float = OVER_BROAD_THRESHOLD) -> list[TermStats]:
    results = []
    for t in terms:
        doc_hits    = int(t.get('doc_hits') or 0)
        family_hits = int(t.get('family_hits') or 0)
        unique_hits = int(t.get('unique_hits') or 0)
        pct         = doc_hits / total_docs if total_docs else 0.0
        f_mult      = family_hits / doc_hits if doc_hits else 0.0
        u_ratio     = unique_hits / doc_hits if doc_hits else 0.0
        errors      = validate_syntax(t.get('term_text', ''),
                                      t.get('syntax', 'dtsearch'))
        flags = []
        if doc_hits == 0:                            flags.append('ZERO HITS')
        if pct > threshold:                          flags.append('OVER-BROAD')
        if doc_hits > 0 and u_ratio < SUBSUMED_THRESHOLD:
                                                     flags.append('SUBSUMED')
        if f_mult > ATTACHMENT_THRESHOLD:            flags.append('ATTACHMENT-HEAVY')
        if errors:                                   flags.append('SYNTAX ERROR')

        results.append(TermStats(
            term_text=t.get('term_text', ''),
            syntax=t.get('syntax', 'dtsearch'),
            doc_hits=doc_hits, family_hits=family_hits,
            unique_hits=unique_hits, total_docs=total_docs,
            pct_of_dataset=round(pct * 100, 1),
            family_multiplier=round(f_mult, 2),
            unique_ratio=round(u_ratio, 2),
            risk_flags=flags, syntax_errors=errors,
            lucene_equivalent=t.get('lucene_equivalent', ''),
            rationale=t.get('rationale', ''),
            proposed_by=t.get('proposed_by', 'pm'),
            status=t.get('status', 'draft'),
        ))
    return results
