"""Generate W/3 proximity search terms for person names with nickname variations."""

import re

NICKNAMES: dict[str, list[str]] = {
    "alexander": ["alex"],
    "andrew": ["andy", "drew"],
    "anthony": ["tony"],
    "benjamin": ["ben"],
    "catherine": ["cathy", "kate", "kathy"],
    "charles": ["charlie", "chuck"],
    "christopher": ["chris"],
    "daniel": ["dan", "danny"],
    "david": ["dave"],
    "deborah": ["deb", "debbie"],
    "donald": ["don"],
    "dorothy": ["dot", "dottie"],
    "edward": ["ed", "eddie", "ted"],
    "elizabeth": ["liz", "beth", "betty"],
    "eugene": ["gene"],
    "frederick": ["fred", "freddy"],
    "gregory": ["greg"],
    "harold": ["hal", "harry"],
    "james": ["jim", "jimmy", "jamie"],
    "jennifer": ["jen", "jenny"],
    "jessica": ["jess", "jessie"],
    "jonathan": ["jon", "john"],
    "joseph": ["joe", "joey"],
    "joshua": ["josh"],
    "katherine": ["kate", "kathy", "katie"],
    "kenneth": ["ken", "kenny"],
    "lawrence": ["larry"],
    "margaret": ["maggie", "meg", "peggy"],
    "matthew": ["matt"],
    "michael": ["mike"],
    "nathaniel": ["nate", "nathan"],
    "nicholas": ["nick"],
    "patricia": ["pat", "patty"],
    "patrick": ["pat"],
    "peter": ["pete"],
    "raymond": ["ray"],
    "richard": ["rick", "rich", "dick"],
    "robert": ["bob", "rob", "bobby"],
    "samuel": ["sam"],
    "stephen": ["steve"],
    "steven": ["steve"],
    "susan": ["sue", "susie"],
    "theodore": ["ted", "teddy"],
    "thomas": ["tom", "tommy"],
    "timothy": ["tim"],
    "victoria": ["vicki", "vicky"],
    "william": ["will", "bill", "billy"],
}

_CORPORATE_SUFFIXES = re.compile(
    r'\b(Inc|LLC|Corp|Ltd|LLP|LP|Co|PLC|NA|NV|SA|AG|GmbH|Group|Holdings)\b',
    re.IGNORECASE,
)


def _is_person_name(entity: str) -> bool:
    """Heuristic: 2-3 capitalized words, no corporate suffixes."""
    if _CORPORATE_SUFFIXES.search(entity):
        return False
    words = entity.split()
    if len(words) < 2 or len(words) > 3:
        return False
    return all(w[0].isupper() and w.isalpha() for w in words)


def generate_name_terms(named_entities: list[str]) -> list[dict]:
    """Generate W/3 proximity terms for person names, including nickname variations.

    Returns dicts matching the standard term schema:
    term_text, lucene_equivalent, rationale, risk_notes, specialist_flag
    """
    results: list[dict] = []
    for entity in named_entities:
        if not _is_person_name(entity):
            continue

        parts = entity.split()
        first = parts[0]
        last = parts[-1]

        first_lower = first.lower()
        last_lower = last.lower()

        # Canonical form: first W/3 last
        dt_term = f"{first_lower} W/3 {last_lower}"
        lucene = f'"{first_lower} {last_lower}"~3'
        results.append({
            "term_text": dt_term,
            "lucene_equivalent": lucene,
            "rationale": f"Proximity search for {entity}",
            "risk_notes": "",
            "specialist_flag": False,
        })

        # Nickname variations
        nicks = NICKNAMES.get(first_lower, [])
        for nick in nicks:
            dt_nick = f"{nick} W/3 {last_lower}"
            lucene_nick = f'"{nick} {last_lower}"~3'
            results.append({
                "term_text": dt_nick,
                "lucene_equivalent": lucene_nick,
                "rationale": f"Nickname variation for {entity} ({nick})",
                "risk_notes": "",
                "specialist_flag": False,
            })

    return results
