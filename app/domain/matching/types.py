from dataclasses import dataclass


@dataclass(frozen=True)
class MatchDecision:
    score: int
    confidence: float
    decision: str
    component_scores: dict[str, int]
    matched_criteria: list[str]
    missing_criteria: list[str]
    concerns: list[str]
    reasoning: str
