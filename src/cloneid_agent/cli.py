"""Command-line interface for deterministic CLONEID agent utilities."""

from __future__ import annotations

import argparse
import sys

from .inventory import run_inventory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cloneid_agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Run the read-only CLONEID database inventory wrapper.",
    )
    inventory_parser.add_argument(
        "--output",
        help="Run output directory. Defaults to runs/<run_id>.",
    )
    inventory_parser.add_argument(
        "--run-id",
        help="Run identifier to use when --output is not provided.",
    )
    inventory_parser.add_argument(
        "--mode",
        choices=("auto", "live", "mock"),
        default="auto",
        help="Inventory mode. 'auto' tries live access and falls back to mock.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inventory":
        return run_inventory(output=args.output, run_id=args.run_id, mode=args.mode)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
