import argparse
import os
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

CATEGORIES = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Performance",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "build": "Build and dependencies",
    "ci": "CI/CD",
    "chore": "Maintenance",
    "test": "Tests",
}


def categorize(subject: str) -> tuple[str, str]:
    prefix, separator, description = subject.partition(":")
    kind = prefix.split("(", 1)[0].lower().strip()
    title = description.strip() if separator else subject.strip()
    return CATEGORIES.get(kind, "Other"), title


def git_subjects(from_ref: str | None, to_ref: str) -> list[str]:
    revision = f"{from_ref}..{to_ref}" if from_ref else to_ref
    result = subprocess.run(
        ["git", "log", "--format=%s", revision], check=True, capture_output=True, text=True
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def render(subjects: list[str], version: str, commit_sha: str, generated_at: str) -> str:
    grouped: dict[str, list[str]] = defaultdict(list)
    for subject in subjects:
        category, title = categorize(subject)
        grouped[category].append(title)
    lines = [
        f"# Release {version}",
        "",
        f"- Commit: `{commit_sha}`",
        f"- Generated: {generated_at}",
        "",
    ]
    for category in (*CATEGORIES.values(), "Other"):
        if grouped.get(category):
            lines.extend([f"## {category}", ""])
            lines.extend(f"- {item}" for item in grouped[category])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate release notes from conventional commits")
    parser.add_argument("--from-ref")
    parser.add_argument("--to-ref", default="HEAD")
    parser.add_argument("--version", default=os.getenv("APP_VERSION", "unreleased"))
    parser.add_argument("--output", default="release-notes.md")
    args = parser.parse_args()
    try:
        sha = subprocess.run(
            ["git", "rev-parse", args.to_ref], check=True, capture_output=True, text=True
        ).stdout.strip()
        subjects = git_subjects(args.from_ref, args.to_ref)
    except subprocess.CalledProcessError:
        ref = args.from_ref or args.to_ref
        print(f"Git ref '{ref}' was not found. Use an existing tag, branch, or commit SHA.")
        return 2
    generated_at = datetime.now(UTC).isoformat()
    notes = render(subjects, args.version, sha, generated_at)
    Path(args.output).write_text(notes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
