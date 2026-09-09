from app.domain.jobs.models import Job
from app.domain.preferences.schemas import PreferenceInput
from app.matching.rule_engine import evaluate_rules
from app.matching.scorer import evaluate_rules as public_evaluate_rules


def job(**kwargs):
    values = dict(
        title="Senior Backend Engineer",
        company_name="Acme",
        company_normalized="acme",
        description="Python PostgreSQL AWS",
        description_hash="x",
        locations=["Mumbai"],
        application_url="https://apply",
    )
    values.update(kwargs)
    return Job(**values)


def test_matching_scores_and_explains_fit():
    preferences = PreferenceInput(
        titles=["Backend Engineer"],
        skills={"must_have": ["Python"], "nice_to_have": ["AWS"]},
        locations={"preferred": ["Mumbai"]},
        companies={"preferred": ["Acme"]},
        matching={"minimum_score": 20},
    )
    result = evaluate_rules(job(), preferences)
    assert result.decision == "notify"
    assert result.score > 0
    assert "Python" in result.matched_criteria
    assert public_evaluate_rules(job(), preferences) == result


def test_matching_rejects_exclusion_and_reports_missing():
    preferences = PreferenceInput(
        titles=["Backend Engineer"],
        skills={"must_have": ["FastAPI"]},
        exclusions=["PHP"],
        matching={"minimum_score": 90},
    )
    result = evaluate_rules(job(description="PHP frontend"), preferences)
    assert result.decision == "reject"
    assert result.concerns == ["PHP"]
    assert result.missing_criteria == ["FastAPI"]
