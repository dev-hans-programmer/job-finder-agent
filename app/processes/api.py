"""API process entrypoint."""

import uvicorn


def main() -> None:  # pragma: no cover
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":  # pragma: no cover
    main()
