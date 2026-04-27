"""Command-line interface for deterministic CLONEID agent utilities."""

from __future__ import annotations

import argparse
import sys

from .dataset_inventory import run_candidate_inventory
from .dataset_ranking import rank_candidates_from_file, write_ranked_candidates
from .dataset_selection import select_top_candidate_from_file, write_selected_candidate
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

    candidate_parser = subparsers.add_parser(
        "candidate-inventory",
        help="Run higher-level candidate-dataset inventory.",
    )
    candidate_parser.add_argument(
        "--output",
        help="Run output directory. Defaults to runs/<run_id>.",
    )
    candidate_parser.add_argument(
        "--run-id",
        help="Run identifier to use when --output is not provided.",
    )
    candidate_parser.add_argument(
        "--mode",
        choices=("auto", "live", "mock"),
        default="auto",
        help="Candidate inventory mode. 'auto' tries live access and falls back to mock.",
    )

    rank_input_kwargs = {
        "required": True,
        "help": "Path to dataset_inventory.json",
    }
    rank_output_kwargs = {
        "required": True,
        "help": "Directory for ranked_candidates.json and ranked_candidates.md",
    }

    rank_parser = subparsers.add_parser(
        "rank-candidates",
        help="Fine-rank candidate datasets from a dataset_inventory.json artifact.",
    )
    rank_parser.add_argument(
        "--input",
        **rank_input_kwargs,
    )
    rank_parser.add_argument(
        "--output-dir",
        **rank_output_kwargs,
    )

    fine_rank_parser = subparsers.add_parser(
        "fine-rank-candidates",
        help="Alias for rank-candidates using the fine-grained ranking model.",
    )
    fine_rank_parser.add_argument(
        "--input",
        **rank_input_kwargs,
    )
    fine_rank_parser.add_argument(
        "--output-dir",
        **rank_output_kwargs,
    )

    select_parser = subparsers.add_parser(
        "select-candidate",
        help="Select the top-ranked candidate dataset from ranked_candidates.json.",
    )
    select_parser.add_argument(
        "--input",
        required=True,
        help="Path to ranked_candidates.json",
    )
    select_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for selected_candidate.json and selected_candidate.md",
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
    if args.command == "candidate-inventory":
        return run_candidate_inventory(output=args.output, run_id=args.run_id, mode=args.mode)
    if args.command in {"rank-candidates", "fine-rank-candidates"}:
        ranked = rank_candidates_from_file(args.input)
        write_ranked_candidates(args.output_dir, ranked)
        return 0
    if args.command == "select-candidate":
        selected = select_top_candidate_from_file(args.input)
        write_selected_candidate(args.output_dir, selected)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
