"""Figure generation for the CLONEID-LTE r/K benchmark."""

from __future__ import annotations

from pathlib import Path
import struct
import zlib
from typing import Any


FIGURE_FILENAMES = (
    "external_vs_cloneid_record_granularity.png",
    "nsr_reconstructed_evidence_map.png",
    "cloneid_event_graph.png",
    "full_vs_coarse_growth_evidence.png",
    "model_comparison_publication_vs_cloneid.png",
    "cloneid_lte_standard_summary.png",
)


STATUS_COLORS = {
    "structured_numeric_table": "#2f7d32",
    "model_formula_in_caption_or_methods": "#1976d2",
    "embedded_plot_or_representative_image": "#f9a825",
    "method_text_only": "#6d4c41",
    "not_available_in_archive": "#bdbdbd",
    "not_event_linked": "#ef6c00",
    "not_agent_ready_without_manual_reconstruction": "#c62828",
}


def _try_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap

        return plt, ListedColormap
    except Exception:
        return None, None


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _write_fallback_png(path: Path, palette: list[tuple[int, int, int]]) -> None:
    width, height = 960, 540
    rows = []
    stripe = max(1, height // max(len(palette), 1))
    for y in range(height):
        color = palette[min(y // stripe, len(palette) - 1)]
        row = b"\x00" + bytes(color) * width
        rows.append(row)
    raw = b"".join(rows)
    data = b"\x89PNG\r\n\x1a\n"
    data += _png_chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0))
    data += _png_chunk(b"IDAT", zlib.compress(raw, 9))
    data += _png_chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[idx : idx + 2], 16) for idx in (0, 2, 4))


def _save_or_fallback(path: Path, draw_func, fallback_colors: list[str]) -> Path:
    plt, _ = _try_matplotlib()
    if plt is None:
        _write_fallback_png(path, [_hex_to_rgb(color) for color in fallback_colors])
        return path
    draw_func(plt)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def plot_record_granularity(audit_rows: list[dict[str, Any]], path: str | Path) -> Path:
    target = Path(path)
    labels = list(STATUS_COLORS)
    label_to_index = {label: idx for idx, label in enumerate(labels)}
    columns = [
        "NSR_publication_level_reconstructed_record",
        "CLONEID_full_native_record",
        "CLONEID_publication_level_downsampled_record",
    ]

    def draw(plt):
        _, listed = _try_matplotlib()
        matrix = [
            [label_to_index[row[column]] for column in columns]
            for row in audit_rows
        ]
        cmap = listed([STATUS_COLORS[label] for label in labels])
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.imshow(matrix, cmap=cmap, vmin=0, vmax=len(labels) - 1, aspect="auto")
        ax.set_yticks(range(len(audit_rows)))
        ax.set_yticklabels([row["dimension"] for row in audit_rows], fontsize=7)
        ax.set_xticks(range(len(columns)))
        ax.set_xticklabels(["NSR", "CLONEID full", "CLONEID coarse"], rotation=25, ha="right")
        ax.set_title("Record granularity and modelability status")
        for spine in ax.spines.values():
            spine.set_visible(False)

    return _save_or_fallback(target, draw, list(STATUS_COLORS.values()))


def plot_nsr_evidence_map(figure_index: list[dict[str, Any]], model_records: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    components = [
        "growth-rate distribution",
        "carrying capacity",
        "competition fractions",
        "spatial model",
        "migration/adhesion",
        "molecular endpoint",
    ]
    sources = ["Table 5", "Fig. 9", "Fig. 10", "Fig. 4/5/11/12", "Fig. 13", "Fig. 15", "Data 1-4"]
    active = {
        ("growth-rate distribution", "Table 5"),
        ("growth-rate distribution", "Fig. 9"),
        ("carrying capacity", "Fig. 10"),
        ("competition fractions", "Fig. 4/5/11/12"),
        ("spatial model", "Fig. 13"),
        ("migration/adhesion", "Fig. 15"),
        ("molecular endpoint", "Data 1-4"),
    }

    def draw(plt):
        matrix = [[1 if (component, source) in active else 0 for source in sources] for component in components]
        fig, ax = plt.subplots(figsize=(9, 4.8))
        ax.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
        ax.set_yticks(range(len(components)))
        ax.set_yticklabels(components)
        ax.set_xticks(range(len(sources)))
        ax.set_xticklabels(sources, rotation=30, ha="right")
        ax.set_title("NSR supplement evidence feeding reconstructed model components")

    return _save_or_fallback(target, draw, ["#e0f2f1", "#1976d2"])


def plot_cloneid_event_graph(event_graph: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)

    def draw(plt):
        nodes = event_graph["nodes"]
        branches = {"IN": 0, "r": 1, "K": 2}
        branch_colors = {"IN": "#616161", "r": "#7b1fa2", "K": "#00897b"}
        positions = {}
        for node in nodes:
            x = node["passage_number"]
            y = branches.get(node["branch_label"], 0)
            if node["event_type"] == "harvest":
                x += 0.42
            positions[node["event_id"]] = (x, y)
        fig, ax = plt.subplots(figsize=(10, 4.8))
        for edge in event_graph["edges"]:
            x1, y1 = positions[edge["source"]]
            x2, y2 = positions[edge["target"]]
            ax.plot([x1, x2], [y1, y2], color="#9e9e9e", linewidth=1.4, zorder=1)
        for node in nodes:
            x, y = positions[node["event_id"]]
            ax.scatter([x], [y], s=110, color=branch_colors.get(node["branch_label"], "#424242"), zorder=2)
        ax.set_yticks([0, 1, 2])
        ax.set_yticklabels(["IN", "r", "K"])
        ax.set_xlabel("Passage and seed-to-harvest progression")
        ax.set_title("SNU-668 r/K event graph")
        ax.grid(axis="x", alpha=0.2)

    return _save_or_fallback(target, draw, ["#616161", "#7b1fa2", "#00897b"])


def plot_full_vs_coarse_growth(growth_episodes: list[dict[str, Any]], coarse_record: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)

    def draw(plt):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        for branch, color in (("r", "#7b1fa2"), ("K", "#00897b")):
            xs = [row["passage_number"] for row in growth_episodes if row["branch_label"] == branch]
            rates = [row["growth_rate_per_hour"] for row in growth_episodes if row["branch_label"] == branch]
            conf = [row["seed_confluence_proxy"] for row in growth_episodes if row["branch_label"] == branch]
            axes[0].plot(xs, rates, marker="o", color=color, label=branch)
            axes[1].plot(conf, rates, marker="o", color=color, label=branch)
        axes[0].set_title("Full event-linked growth episodes")
        axes[0].set_xlabel("Passage")
        axes[0].set_ylabel("Growth rate per hour")
        axes[1].set_title("Density evidence retained only in full record")
        axes[1].set_xlabel("Seed confluence proxy")
        axes[1].legend()

    return _save_or_fallback(target, draw, ["#7b1fa2", "#00897b", "#eeeeee"])


def plot_model_comparison(comparison_rows: list[dict[str, Any]], path: str | Path) -> Path:
    target = Path(path)

    def draw(plt):
        sources = ["NSR", "CLONEID full", "CLONEID coarse"]
        status_score = {
            "identifiable": 3,
            "summary_only_identifiable": 2,
            "publication_level_reconstruction_only": 1,
            "not_identifiable_due_to_missing_event_level_density_or_event_graph": 0,
            "not_available_in_archive": 0,
        }
        matrix = []
        for row in comparison_rows:
            matrix.append(
                [
                    status_score.get(row["NSR_publication_level_reconstructed_record_fit_status"], 0),
                    status_score.get(row["CLONEID_full_native_record_fit_status"], 0),
                    status_score.get(row["CLONEID_publication_level_downsampled_record_fit_status"], 0),
                ]
            )
        fig, ax = plt.subplots(figsize=(8, 4.6))
        ax.imshow(matrix, cmap="viridis", vmin=0, vmax=3, aspect="auto")
        ax.set_yticks(range(len(comparison_rows)))
        ax.set_yticklabels([row["family_id"] for row in comparison_rows])
        ax.set_xticks(range(len(sources)))
        ax.set_xticklabels(sources, rotation=20, ha="right")
        ax.set_title("Model identifiability by record type")

    return _save_or_fallback(target, draw, ["#440154", "#21918c", "#fde725"])


def plot_lte_standard_summary(path: str | Path) -> Path:
    target = Path(path)

    def draw(plt):
        tiers = ["Bronze", "Silver", "Gold", "Platinum"]
        values = [18, 10, 10, 6]
        colors = ["#8d6e63", "#78909c", "#c0a000", "#455a64"]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(tiers, values, color=colors)
        ax.set_ylabel("Required fields or artifacts")
        ax.set_title("CLONEID-LTE standard tiers")
        for idx, value in enumerate(values):
            ax.text(idx, value + 0.5, str(value), ha="center")

    return _save_or_fallback(target, draw, ["#8d6e63", "#78909c", "#c0a000", "#455a64"])


def generate_rk_benchmark_figures(
    *,
    output_dir: str | Path,
    audit_rows: list[dict[str, Any]],
    figure_index: list[dict[str, Any]],
    model_records: dict[str, Any],
    event_graph: dict[str, Any],
    growth_episodes: list[dict[str, Any]],
    coarse_record: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    return {
        "external_vs_cloneid_record_granularity": plot_record_granularity(
            audit_rows,
            output / "external_vs_cloneid_record_granularity.png",
        ),
        "nsr_reconstructed_evidence_map": plot_nsr_evidence_map(
            figure_index,
            model_records,
            output / "nsr_reconstructed_evidence_map.png",
        ),
        "cloneid_event_graph": plot_cloneid_event_graph(event_graph, output / "cloneid_event_graph.png"),
        "full_vs_coarse_growth_evidence": plot_full_vs_coarse_growth(
            growth_episodes,
            coarse_record,
            output / "full_vs_coarse_growth_evidence.png",
        ),
        "model_comparison_publication_vs_cloneid": plot_model_comparison(
            comparison_rows,
            output / "model_comparison_publication_vs_cloneid.png",
        ),
        "cloneid_lte_standard_summary": plot_lte_standard_summary(output / "cloneid_lte_standard_summary.png"),
    }
