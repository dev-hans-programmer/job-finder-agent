from collections import Counter

_metrics: Counter[str] = Counter()


def increment(name: str, value: int = 1) -> None:
    _metrics[name] += value


def snapshot() -> dict[str, int]:
    return dict(_metrics)


def prometheus() -> str:
    return "\n".join(f"jobradar_{key} {value}" for key, value in sorted(_metrics.items())) + "\n"
