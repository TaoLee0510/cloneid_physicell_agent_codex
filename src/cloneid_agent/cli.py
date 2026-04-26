"""Command-line interface for deterministic CLONEID agent utilities."""

from __future__ import annotations

import argparse
import sys

from .inventory import run_inventory
from .toy_workflow import run_toy_round_trip


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

    toy_parser = subparsers.add_parser(
        "toy-roundtrip",
        help="Write a synthetic CLONEID-like dry-run artifact set.",
    )
    toy_parser.add_argument(
        "--output",
        help="Run output directory. Defaults to runs/<run_id>.",
    )
    toy_parser.add_argument(
        "--run-id",
        help="Run identifier to use when --output is not provided.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inventory":
        return run_inventory(output=args.output, run_id=args.run_id, mode=args.mode)
    if args.command == "toy-roundtrip":
        run_toy_round_trip(output=args.output, run_id=args.run_id)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
