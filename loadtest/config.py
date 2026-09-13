import os
from dataclasses import dataclass


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True)
class LoadTestConfig:
    target_url: str
    email_prefix: str
    password: str
    source_id: str | None
    wait_min: int
    wait_max: int

    @classmethod
    def from_env(cls) -> "LoadTestConfig":
        wait_min = _positive_int("LOADTEST_WAIT_MIN", 1)
        wait_max = _positive_int("LOADTEST_WAIT_MAX", 3)
        if wait_max < wait_min:
            raise ValueError("LOADTEST_WAIT_MAX must be greater than or equal to LOADTEST_WAIT_MIN")
        return cls(
            target_url=os.getenv("LOADTEST_TARGET_URL", "http://localhost:8000").rstrip("/"),
            email_prefix=os.getenv("LOADTEST_EMAIL_PREFIX", "loadtest"),
            password=os.getenv("LOADTEST_PASSWORD", "LoadTestPassword123!"),
            source_id=os.getenv("LOADTEST_SOURCE_ID") or None,
            wait_min=wait_min,
            wait_max=wait_max,
        )
