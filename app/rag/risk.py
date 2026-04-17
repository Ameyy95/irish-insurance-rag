from dataclasses import dataclass


HIGH_RISK_PATTERNS = [
    "capital adequacy",
    "solvency",
    "solvency ii",
    "solvency capital requirement",
    "scr",
    "mcr",
    "minimum capital requirement",
    "aml",
    "anti-money laundering",
    "breach reporting",
    "suspicious transaction",
    "suspicious activity",
    "str",
]


@dataclass(frozen=True)
class RiskAssessment:
    level: str  # low | high
    reason: str


def assess_risk(question: str) -> RiskAssessment:
    q = (question or "").lower()
    for pat in HIGH_RISK_PATTERNS:
        if pat in q:
            return RiskAssessment(level="high", reason=f"Matched high-risk pattern: {pat}")
    return RiskAssessment(level="low", reason="No high-risk patterns matched")

