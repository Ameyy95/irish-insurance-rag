import re
from functools import lru_cache

import spacy


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}\b")


@lru_cache(maxsize=1)
def _nlp():
    return spacy.load("en_core_web_sm")


def redact_pii(text: str) -> str:
    if not text:
        return text

    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", redacted)

    doc = _nlp()(redacted)
    spans = []
    for ent in doc.ents:
        if ent.label_ in {"PERSON", "GPE", "LOC", "ORG"}:
            spans.append((ent.start_char, ent.end_char, f"[REDACTED_{ent.label_}]"))

    if not spans:
        return redacted

    spans.sort(key=lambda x: x[0])
    out = []
    last = 0
    for start, end, repl in spans:
        if start < last:
            continue
        out.append(redacted[last:start])
        out.append(repl)
        last = end
    out.append(redacted[last:])
    return "".join(out)

