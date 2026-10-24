"""Mask personal data in text before it's written to logs.

Questions are logged for debugging (original and rewritten query), and users sometimes paste emails, phone
numbers or account numbers into them. Logs are kept by the host, so those are masked first. This is
pattern-based (no names or addresses), aimed at the identifiers that are easy to detect and costly to leak.
"""

import re

_PATTERNS = [
    ("[email]", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("[card]", re.compile(r"\b\d(?:[ -]?\d){12,18}\b")),
    ("[ip]", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("[phone]", re.compile(r"(?<![\w(])\+?\(?\d[\d ().-]{7,}\d(?!\w)")),
    ("[number]", re.compile(r"\b\d{6,}\b")),  # account, ID or order numbers
]


def redact(text: str) -> str:
    for label, pattern in _PATTERNS:
        text = pattern.sub(label, text)
    return text
