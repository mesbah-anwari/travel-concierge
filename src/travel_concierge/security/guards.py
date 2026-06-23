"""Security layer for the Travel Concierge.

Implements four guardrails required by the Capstone course:

1. Input validation (length, charset, basic shape).
2. Prompt-injection detection (heuristic).
3. PII redaction on outputs (emails, phones, credit cards, SSNs, API keys).
4. Output safety / unsafe-content filter (categories blocklist).

All checks are pure-Python and dependency-free so they can run inside a
Kaggle notebook with no extra installs. They are deliberately conservative —
on any doubt, the call is blocked and a safe fallback message returned.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 1. Input validation
# ---------------------------------------------------------------------------

MAX_INPUT_CHARS = 4_000
ALLOWED_CTRL = {"\n", "\r", "\t"}


@dataclass
class ValidationResult:
    ok: bool
    cleaned: str
    reason: str = ""


def validate_user_input(text: str) -> ValidationResult:
    """Reject empty, too-long, or control-character-laden inputs."""
    if text is None:
        return ValidationResult(False, "", "empty input")
    text = text.strip()
    if not text:
        return ValidationResult(False, "", "empty input")
    if len(text) > MAX_INPUT_CHARS:
        return ValidationResult(
            False, "", f"input exceeds {MAX_INPUT_CHARS} characters"
        )
    bad = [c for c in text if ord(c) < 32 and c not in ALLOWED_CTRL]
    if bad:
        return ValidationResult(False, "", "input contains control characters")
    return ValidationResult(True, text)


# ---------------------------------------------------------------------------
# 2. Prompt-injection guard
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS = [
    r"ignore (all|any|the)? ?(previous|prior|above) (instructions|prompt)s?",
    r"disregard (all|any|the)? ?(previous|prior|above) (instructions|prompt)s?",
    r"you are now (a|an) [a-z ]*?(model|assistant|agent|ai)",
    r"(with no|without) (restrictions|guardrails|filter|filters|safety)",
    r"system prompt[: ]",
    r"reveal (your|the) (system prompt|instructions|hidden)",
    r"jailbreak",
    r"developer mode",
    r"\bDAN mode\b",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def detect_prompt_injection(text: str) -> bool:
    """Return True if the input looks like a prompt-injection attempt."""
    return bool(_INJECTION_RE.search(text or ""))


# ---------------------------------------------------------------------------
# 3. PII redaction
# ---------------------------------------------------------------------------

_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "GOOGLE_KEY": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "OPENAI_KEY": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    # 13-19 digits with optional separators, Luhn-checked below
    "CARD": re.compile(r"\b(?:\d[ -]?){12,18}\d\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # Phones: shorter sequences (8-13 digits incl. separators) to avoid
    # collisions with credit cards (which are already redacted above).
    "PHONE": re.compile(r"\+?\d[\d \-().]{6,12}\d"),
}


def _luhn(num: str) -> bool:
    digits = [int(c) for c in num if c.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


_DIGIT_NEIGHBOR = re.compile(r"[\d\-\s]")


def redact_pii(text: str) -> str:
    """Mask common PII tokens in any agent output before showing the user.

    Patterns are applied in the dict order; sensitive tokens that overlap
    with phone numbers (credit cards, API keys) are redacted first so the
    phone pattern only sees the leftovers. The phone callback rejects any
    match whose digit count is outside 7-13, and also rejects matches that
    are clearly part of a longer adjacent digit sequence (e.g. a card-shaped
    string that failed Luhn).
    """
    if not text:
        return text
    out = text
    for label, pat in _PII_PATTERNS.items():
        def _sub(m: re.Match[str], _label: str = label, _text: str = out) -> str:
            value = m.group(0)
            if _label == "CARD" and not _luhn(value):
                return value
            if _label == "PHONE":
                n_digits = sum(c.isdigit() for c in value)
                if n_digits < 7 or n_digits > 13:
                    return value
                before = _text[max(0, m.start() - 2):m.start()]
                after = _text[m.end():m.end() + 2]
                if any(_DIGIT_NEIGHBOR.fullmatch(c) for c in before) and \
                   any(_DIGIT_NEIGHBOR.fullmatch(c) for c in after):
                    # Looks like part of a longer digit block — skip.
                    return value
            return f"[REDACTED_{_label}]"
        out = pat.sub(_sub, out)
    return out


# ---------------------------------------------------------------------------
# 4. Output safety / unsafe-content filter
# ---------------------------------------------------------------------------

_UNSAFE_PATTERNS = [
    r"\b(?:bomb|explosive|detonator)\s+(?:recipe|instructions|how to)",
    r"how to (?:make|build|synthesize) (?:meth|fentanyl|heroin)",
    r"child sexual abuse",
    r"kill yourself",
]
_UNSAFE_RE = re.compile("|".join(_UNSAFE_PATTERNS), re.IGNORECASE)


def is_unsafe_output(text: str) -> bool:
    """Return True if the output contains disallowed content."""
    return bool(_UNSAFE_RE.search(text or ""))


# ---------------------------------------------------------------------------
# Composite guard
# ---------------------------------------------------------------------------


@dataclass
class GuardResult:
    allowed: bool
    text: str
    reason: str = ""


def guard_input(raw: str) -> GuardResult:
    v = validate_user_input(raw)
    if not v.ok:
        return GuardResult(False, "", v.reason)
    if detect_prompt_injection(v.cleaned):
        return GuardResult(
            False,
            "",
            "input matched a known prompt-injection pattern; request blocked",
        )
    return GuardResult(True, v.cleaned)


def guard_output(raw: str) -> GuardResult:
    if is_unsafe_output(raw):
        return GuardResult(
            False,
            "I can't share that information. Please ask something travel-related.",
            "unsafe content blocked",
        )
    return GuardResult(True, redact_pii(raw))
