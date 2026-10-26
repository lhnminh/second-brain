"""Visual Second Brain backend."""


def main() -> None:
    import uvicorn

    uvicorn.run("second_brain.api:create_app", factory=True, port=8000)
