import uuid

from locust import HttpUser, between, task

from loadtest.config import LoadTestConfig


class JobRadarUser(HttpUser):
    """A realistic read-heavy user with optional ingestion activity."""

    config = LoadTestConfig.from_env()
    wait_time = between(config.wait_min, config.wait_max)

    def on_start(self) -> None:
        self.token: str | None = None
        email = f"{self.config.email_prefix}+{uuid.uuid4().hex}@example.com"
        with self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": self.config.password},
            name="POST /auth/register",
            catch_response=True,
        ) as response:
            if response.status_code not in {201, 409}:
                response.failure(f"registration returned {response.status_code}")
        with self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": self.config.password},
            name="POST /auth/login",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                self.token = response.json().get("data", {}).get("access_token")
            else:
                response.failure(f"login returned {response.status_code}")

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(8)
    def list_jobs(self) -> None:
        self.client.get("/api/v1/jobs", headers=self.headers, name="GET /jobs")

    @task(3)
    def get_current_user(self) -> None:
        self.client.get("/api/v1/auth/me", headers=self.headers, name="GET /auth/me")

    @task(2)
    def list_sources(self) -> None:
        self.client.get("/api/v1/sources", headers=self.headers, name="GET /sources")

    @task(1)
    def run_source(self) -> None:
        if self.config.source_id:
            self.client.post(
                f"/api/v1/sources/{self.config.source_id}/run",
                headers=self.headers,
                name="POST /sources/{id}/run",
            )

    @task(1)
    def health_check(self) -> None:
        self.client.get("/health/live", name="GET /health/live")
