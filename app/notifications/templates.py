from app.domain.jobs.models import Job
from app.domain.matching.models import MatchResult


def render_match(job: Job, match: MatchResult) -> tuple[str, str]:
    subject = f"Job match: {job.title} at {job.company_name} ({match.score}/100)"
    body = (
        f"Score: {match.score}/100\nTitle: {job.title}\nCompany: {job.company_name}\n"
        f"Location: {', '.join(job.locations)}\nWork mode: {job.work_mode}\n"
        f"Matched: {', '.join(match.matched_criteria) or 'none'}\n"
        f"Missing: {', '.join(match.missing_criteria) or 'none'}\n"
        f"Concerns: {', '.join(match.concerns) or 'none'}\nApply: {job.application_url}"
    )
    return subject, body
