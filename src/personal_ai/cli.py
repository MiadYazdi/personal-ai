from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

import uvicorn

from .api.app import build_status_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="personal-ai",
        description="Personal AI local-first development CLI.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "status",
        help="Show local Personal AI status without starting a server.",
    )

    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the local-only FastAPI backend.",
    )
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", default=8765, type=int)
    serve_parser.add_argument("--reload", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        print(json.dumps(build_status_payload(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "serve":
        uvicorn.run(
            "personal_ai.api.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
