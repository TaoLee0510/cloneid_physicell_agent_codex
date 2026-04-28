"""Command-line interface for deterministic CLONEID agent utilities."""

from __future__ import annotations

import argparse
import sys

from .dataset_inventory import run_candidate_inventory
from .dataset_ranking import rank_candidates_from_file, write_ranked_candidates
from .dataset_selection import select_top_candidate_from_file, write_selected_candidate
from .inventory import run_inventory
from .lineage_object_pipeline import discover_rank_and_select_lineage_objects
from .lineage_object_ranking import rank_lineage_objects_from_file, write_ranked_lineage_objects
from .lineage_object_selection import (
    select_top_lineage_object_from_file,
    write_selected_lineage_object,
)
from .lineage_objects import discover_global_lineage_objects_from_file, write_global_lineage_inventory
from .observable_selection import select_observables_from_bundle_file, write_selected_observables
from .physicell_mapping import build_physicell_mapping_from_files, write_physicell_mapping
from .toy_workflow import run_toy_round_trip
from .trajectory_bundle_pipeline import discover_and_rank_trajectory_bundles
from .trajectory_bundle_ranking import (
    rank_trajectory_bundles_from_files,
    write_ranked_trajectory_bundles,
)
from .trajectory_bundle_selection import (
    select_top_trajectory_bundle_from_file,
    write_selected_trajectory_bundle,
)
from .trajectory_bundles import discover_trajectory_bundle_from_file, write_trajectory_bundle


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

    bundle_parser = subparsers.add_parser(
        "discover-trajectory-bundle",
        help="Discover a connected TrajectoryBundle from a mock or cached record fixture.",
    )
    bundle_parser.add_argument(
        "--input",
        required=True,
        help="Path to a JSON fixture containing passaging, perspective, and optional identity records.",
    )
    bundle_parser.add_argument(
        "--seed-dataset-id",
        required=True,
        help="CandidateSegment dataset_id to use as the seed for graph expansion.",
    )
    bundle_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for trajectory_bundle.json and trajectory_bundle.md",
    )

    rank_bundle_parser = subparsers.add_parser(
        "rank-trajectory-bundles",
        help="Rank one or more discovered TrajectoryBundle payloads.",
    )
    rank_bundle_parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="One or more trajectory_bundle.json paths.",
    )
    rank_bundle_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for ranked_trajectory_bundles.json and ranked_trajectory_bundles.md",
    )

    live_bundle_parser = subparsers.add_parser(
        "discover-live-trajectory-bundles",
        help="Export seed record fixtures through the approved cloneid R interface, discover TrajectoryBundles, and rank them.",
    )
    live_bundle_parser.add_argument(
        "--ranked-candidates",
        required=True,
        help="Path to ranked_candidates.json",
    )
    live_bundle_parser.add_argument(
        "--output",
        help="Run output directory. Defaults to runs/<run_id>.",
    )
    live_bundle_parser.add_argument(
        "--run-id",
        help="Run identifier to use when --output is not provided.",
    )
    live_bundle_parser.add_argument(
        "--mode",
        choices=("live", "mock"),
        default="live",
        help="Use live cloneid DB export or mock fixture export.",
    )
    live_bundle_parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of top-ranked CandidateSegments to use as TrajectoryBundle seeds.",
    )

    select_bundle_parser = subparsers.add_parser(
        "select-trajectory-bundle",
        help="Select the top-ranked TrajectoryBundle and write a bundled record artifact.",
    )
    select_bundle_parser.add_argument(
        "--input",
        required=True,
        help="Path to ranked_trajectory_bundles.json",
    )
    select_bundle_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for selected_trajectory_bundle artifacts",
    )

    observables_parser = subparsers.add_parser(
        "select-observables",
        help="Select calibration and validation observables from a selected TrajectoryBundle artifact.",
    )
    observables_parser.add_argument(
        "--input",
        required=True,
        help="Path to selected_trajectory_bundle.json",
    )
    observables_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for selected_observables artifacts",
    )

    mapping_parser = subparsers.add_parser(
        "map-to-physicell",
        help="Build a first-pass CLONEID-to-PhysiCell mapping from selected bundle artifacts.",
    )
    mapping_parser.add_argument(
        "--bundle",
        required=True,
        help="Path to selected_trajectory_bundle.json",
    )
    mapping_parser.add_argument(
        "--observables",
        required=True,
        help="Path to selected_observables.json",
    )
    mapping_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for physicell_mapping artifacts",
    )

    discover_lineage_parser = subparsers.add_parser(
        "discover-lineage-objects",
        help="Discover global lineage objects from a full-record fixture and annotate them with CandidateSegment scores.",
    )
    discover_lineage_parser.add_argument(
        "--input",
        required=True,
        help="Path to a JSON fixture containing full passaging, perspective, and optional identity records.",
    )
    discover_lineage_parser.add_argument(
        "--ranked-candidates",
        help="Optional ranked_candidates.json path for CandidateSegment score annotations.",
    )
    discover_lineage_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for global_lineage_object_inventory artifacts",
    )

    rank_lineage_parser = subparsers.add_parser(
        "rank-lineage-objects",
        help="Rank globally discovered lineage objects.",
    )
    rank_lineage_parser.add_argument(
        "--input",
        required=True,
        help="Path to global_lineage_object_inventory.json",
    )
    rank_lineage_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for ranked_lineage_objects artifacts",
    )

    select_lineage_parser = subparsers.add_parser(
        "select-lineage-object",
        help="Select the top-ranked global lineage object.",
    )
    select_lineage_parser.add_argument(
        "--input",
        required=True,
        help="Path to ranked_lineage_objects.json",
    )
    select_lineage_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for selected_lineage_object artifacts",
    )

    live_lineage_parser = subparsers.add_parser(
        "discover-live-lineage-objects",
        help="Export full CLONEID records, discover global lineage objects, rank them, and select one lineage object.",
    )
    live_lineage_parser.add_argument(
        "--ranked-candidates",
        required=True,
        help="Path to ranked_candidates.json used only for CandidateSegment score annotations.",
    )
    live_lineage_parser.add_argument(
        "--output",
        help="Run output directory. Defaults to runs/<run_id>.",
    )
    live_lineage_parser.add_argument(
        "--run-id",
        help="Run identifier to use when --output is not provided.",
    )
    live_lineage_parser.add_argument(
        "--mode",
        choices=("live", "mock"),
        default="live",
        help="Use live cloneid DB export or mock full-record export.",
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
    if args.command == "discover-trajectory-bundle":
        bundle = discover_trajectory_bundle_from_file(args.input, args.seed_dataset_id)
        write_trajectory_bundle(args.output_dir, bundle)
        return 0
    if args.command == "rank-trajectory-bundles":
        ranked = rank_trajectory_bundles_from_files(args.input)
        write_ranked_trajectory_bundles(args.output_dir, ranked)
        return 0
    if args.command == "discover-live-trajectory-bundles":
        discover_and_rank_trajectory_bundles(
            ranked_candidates_path=args.ranked_candidates,
            output=args.output,
            run_id=args.run_id,
            mode=args.mode,
            top_n=args.top_n,
        )
        return 0
    if args.command == "select-trajectory-bundle":
        selected = select_top_trajectory_bundle_from_file(args.input)
        write_selected_trajectory_bundle(args.output_dir, selected)
        return 0
    if args.command == "select-observables":
        observables = select_observables_from_bundle_file(args.input)
        write_selected_observables(args.output_dir, observables)
        return 0
    if args.command == "map-to-physicell":
        mapping = build_physicell_mapping_from_files(args.bundle, args.observables)
        write_physicell_mapping(args.output_dir, mapping)
        return 0
    if args.command == "discover-lineage-objects":
        ranked_payload = None
        if args.ranked_candidates:
            import json
            from pathlib import Path

            ranked_payload = json.loads(Path(args.ranked_candidates).read_text())
        inventory = discover_global_lineage_objects_from_file(args.input, ranked_candidates_payload=ranked_payload)
        write_global_lineage_inventory(args.output_dir, inventory)
        return 0
    if args.command == "rank-lineage-objects":
        ranked = rank_lineage_objects_from_file(args.input)
        write_ranked_lineage_objects(args.output_dir, ranked)
        return 0
    if args.command == "select-lineage-object":
        selected = select_top_lineage_object_from_file(args.input)
        write_selected_lineage_object(args.output_dir, selected)
        return 0
    if args.command == "discover-live-lineage-objects":
        discover_rank_and_select_lineage_objects(
            ranked_candidates_path=args.ranked_candidates,
            output=args.output,
            run_id=args.run_id,
            mode=args.mode,
        )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
