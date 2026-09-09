from app.domain.matching.service import MatchingService


def get_matching_service() -> MatchingService:
    return MatchingService()
