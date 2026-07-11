"""
Persian Negation Detector
Handles: نیستم / ندارم / نه اینکه / نه که / prefix نا
"""
import json
import os

_kw_path = os.path.join(os.path.dirname(__file__), "keywords.json")
with open(_kw_path, encoding="utf-8") as f:
    _NEG = json.load(f)["negation"]

NEGATION_PATTERNS: list[str] = _NEG["patterns"]
NEGATION_PREFIXES: list[str] = _NEG["prefixes"]
CONTEXT_WINDOW = 25   # chars to look before the keyword


def is_negated(text: str, keyword: str) -> bool:
    """
    Return True if `keyword` appears negated inside `text`.

    Strategy:
      1. Find keyword position
      2. Look at CONTEXT_WINDOW chars before it for negation patterns
      3. Check if keyword itself starts with a negation prefix
    """
    idx = text.find(keyword)
    if idx == -1:
        return False

    before = text[max(0, idx - CONTEXT_WINDOW): idx]

    for pattern in NEGATION_PATTERNS:
        if pattern in before:
            return True

    for prefix in NEGATION_PREFIXES:
        if keyword.startswith(prefix):
            return True

    return False