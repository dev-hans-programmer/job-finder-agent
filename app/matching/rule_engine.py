from app.domain.jobs.models import Job
from app.domain.matching.types import MatchDecision
from app.domain.preferences.schemas import PreferenceInput

WEIGHTS = {"skills": 40, "experience": 20, "location": 15, "role": 10, "salary": 10, "company": 5}


def evaluate_rules(job: Job, preferences: PreferenceInput) -> MatchDecision:
    text = f"{job.title} {job.description}".casefold()
    concerns = [term for term in preferences.exclusions if term.casefold() in text]
    matched = [
        skill
        for skill in preferences.skills.must_have + preferences.skills.nice_to_have
        if skill.casefold() in text
    ]
    missing = [skill for skill in preferences.skills.must_have if skill.casefold() not in text]
    role = (
        10 if any(title.casefold() in job.title.casefold() for title in preferences.titles) else 0
    )
    location = (
        15
        if any(
            value.casefold() in " ".join(job.locations).casefold()
            for value in preferences.locations.preferred
        )
        else 0
    )
    skills = min(
        40,
        int(
            len(matched)
            / max(1, len(preferences.skills.must_have + preferences.skills.nice_to_have))
            * 40
        ),
    )
    company = (
        5
        if job.company_name.casefold()
        in {name.casefold() for name in preferences.companies.preferred}
        else 0
    )
    score = role + location + skills + company
    if concerns:
        decision = "reject"
        score = 0
    else:
        decision = "notify" if score >= preferences.matching.minimum_score else "review"
    return MatchDecision(
        score,
        0.8,
        decision,
        {
            "skills": skills,
            "experience": 0,
            "location": location,
            "role": role,
            "salary": 0,
            "company": company,
        },
        matched,
        missing,
        concerns,
        "Rule-based match evaluation",
    )
