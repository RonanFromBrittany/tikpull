"""Entry point for the tikpull web server."""

import uvicorn


def main() -> None:
    uvicorn.run(
        "tikpull.web.app:app",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )


if __name__ == "__main__":
    main()
