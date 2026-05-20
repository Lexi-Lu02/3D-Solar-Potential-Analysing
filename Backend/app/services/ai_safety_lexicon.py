"""
Keyword / regex lexicon used by `ai_safety.check_output`.

Plain constants module - tune it without touching code elsewhere. Lists
cover English and Chinese.

Matching (see `ai_safety.py`): BANNED_* is case-insensitive substring match;
LEAK_PATTERNS is compiled regex. Best-effort, not exhaustive - the
self-critique pass is the second line of defence.
"""

from __future__ import annotations

import re

# --- Forbidden content categories ---------------------------------------------

BANNED_SEXUAL = [
    # English
    "porn", "pornographic", "nude", "nudity", "explicit sex", "erotic",
    "sexual intercourse", "blowjob", "masturbat",
    # Chinese
    "色情", "黄片", "做爱", "性爱", "性交", "裸体", "情色", "成人内容",
]

BANNED_VIOLENCE = [
    "how to kill", "how to murder", "build a bomb", "make a bomb",
    "improvised explosive", "shoot up", "mass shooting",
    "杀人", "谋杀", "制造炸弹", "造炸弹", "枪击", "爆炸装置",
]

BANNED_HATE = [
    # slurs / discrimination triggers - keep it small and obvious,
    # self-critique handles the long tail
    "racial slur", "ethnic slur", "hate speech",
    "种族歧视", "民族歧视", "仇恨言论",
]

BANNED_SELF_HARM = [
    "how to commit suicide", "kill myself", "ways to die",
    "自杀方法", "怎么自杀", "怎样自杀", "自残方法",
]

BANNED_ILLEGAL = [
    "buy drugs", "sell drugs", "synthesize meth", "money laundering",
    "hack into", "ddos attack", "ransomware code",
    "毒品交易", "贩毒", "洗钱", "黑客攻击", "勒索软件",
]

BANNED_POLITICAL = [
    # no political stances - refuse to discuss
    "天安门", "六四", "法轮功", "tiananmen massacre", "falun gong",
]

BANNED_OFF_TOPIC = [
    # common attempts to drag the assistant off-domain
    "medical diagnosis", "legal advice", "investment advice",
    "psychological counseling",
    "医疗诊断", "法律建议", "投资建议", "心理咨询",
]

ALL_BANNED_PHRASES: list[str] = (
    BANNED_SEXUAL
    + BANNED_VIOLENCE
    + BANNED_HATE
    + BANNED_SELF_HARM
    + BANNED_ILLEGAL
    + BANNED_POLITICAL
    + BANNED_OFF_TOPIC
)


# --- Leak / format patterns ----------------------------------------------------
# stuff that should NEVER show up in a user-facing answer

LEAK_PATTERNS: list[re.Pattern[str]] = [
    # SQL statement - need a SQL-ish neighbour so "select the building" is fine
    re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER)\s+(\*|FROM\b|INTO\b|TABLE\b)", re.IGNORECASE),
    # API-key prefixes
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}\b"),
    re.compile(r"\bDASHSCOPE_API_KEY\b", re.IGNORECASE),
    # filesystem paths - smell like a stack trace / internals leak
    re.compile(r"[A-Za-z]:\\Users\\"),
    re.compile(r"/Backend/app/"),
    re.compile(r'\bFile "[^"]+", line \d+'),  # Python traceback marker
    re.compile(r"\bTraceback \(most recent call last\):"),
]


# --- PII patterns -------------------------------------------------------------
# scrubbed from model output - solar/building data never needs these

PII_PATTERNS: list[re.Pattern[str]] = [
    # email
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # China mainland 11-digit mobile
    re.compile(r"\b1[3-9]\d{9}\b"),
    # Australian mobile (04xx xxx xxx, various separators)
    re.compile(r"\b04\d{2}[\s-]?\d{3}[\s-]?\d{3}\b"),
    # China national ID (18 digits, last may be X)
    re.compile(r"\b\d{17}[\dXx]\b"),
]
