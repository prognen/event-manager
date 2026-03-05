#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MODE_ORDER = [
    "no_tracing_info",
    "tracing_info",
    "no_tracing_debug",
    "tracing_debug",
]


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_stat(stats: dict[str, Any] | None, metric: str) -> float | None:
    if not isinstance(stats, dict):
        return None
    value = stats.get(metric)
    if isinstance(value, int | float):
        return float(value)
    return None


def build_mode_summary(results_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    modes: dict[str, Any] = {}
    tracing_components: dict[str, Any] = {}

    for mode in MODE_ORDER:
        resources_path = results_dir / f"{mode}_resources_report.json"
        full_path = results_dir / f"{mode}_resources_full_report.json"

        resources_report = load_json(resources_path) or {}
        full_report = load_json(full_path) or {}

        cpu_median = get_stat(resources_report.get("cpu"), "median")
        ram_median = get_stat(resources_report.get("ram_mb"), "median")

        modes[mode] = {
            "resources_report": str(resources_path),
            "cpu_median": cpu_median,
            "ram_mb_median": ram_median,
        }

        summary = full_report.get("summary", {}) if isinstance(full_report, dict) else {}
        app_stats = summary.get("app", {}) if isinstance(summary, dict) else {}
        tracing_stats = (
            summary.get("tracing_monitoring", {}) if isinstance(summary, dict) else {}
        )

        if app_stats or tracing_stats:
            tracing_components[mode] = {
                "app": {
                    "cpu_median": get_stat(app_stats.get("cpu"), "median"),
                    "ram_mb_median": get_stat(app_stats.get("ram_mb"), "median"),
                },
                "tracing_monitoring": {
                    "cpu_median": get_stat(tracing_stats.get("cpu"), "median"),
                    "ram_mb_median": get_stat(tracing_stats.get("ram_mb"), "median"),
                },
                "resources_full_report": str(full_path),
            }

    return modes, tracing_components


def delta(current: float | None, base: float | None) -> float | None:
    if current is None or base is None:
        return None
    return current - base


def build_deltas(modes: dict[str, Any]) -> dict[str, Any]:
    return {
        "tracing_overhead_info": {
            "cpu_median_delta": delta(
                modes["tracing_info"]["cpu_median"], modes["no_tracing_info"]["cpu_median"]
            ),
            "ram_mb_median_delta": delta(
                modes["tracing_info"]["ram_mb_median"],
                modes["no_tracing_info"]["ram_mb_median"],
            ),
        },
        "tracing_overhead_debug": {
            "cpu_median_delta": delta(
                modes["tracing_debug"]["cpu_median"], modes["no_tracing_debug"]["cpu_median"]
            ),
            "ram_mb_median_delta": delta(
                modes["tracing_debug"]["ram_mb_median"],
                modes["no_tracing_debug"]["ram_mb_median"],
            ),
        },
        "logging_overhead_without_tracing": {
            "cpu_median_delta": delta(
                modes["no_tracing_debug"]["cpu_median"],
                modes["no_tracing_info"]["cpu_median"],
            ),
            "ram_mb_median_delta": delta(
                modes["no_tracing_debug"]["ram_mb_median"],
                modes["no_tracing_info"]["ram_mb_median"],
            ),
        },
        "logging_overhead_with_tracing": {
            "cpu_median_delta": delta(
                modes["tracing_debug"]["cpu_median"], modes["tracing_info"]["cpu_median"]
            ),
            "ram_mb_median_delta": delta(
                modes["tracing_debug"]["ram_mb_median"], modes["tracing_info"]["ram_mb_median"]
            ),
        },
    }


def f2(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def write_markdown(
    output_path: Path,
    modes: dict[str, Any],
    deltas: dict[str, Any],
    tracing_components: dict[str, Any],
) -> None:
    lines: list[str] = []
    lines.append("# Lab5 comparison report")
    lines.append("")
    lines.append("## Modes (app resource medians)")
    lines.append("")
    lines.append("| Mode | CPU median (%) | RAM median (MB) |")
    lines.append("|---|---:|---:|")
    for mode in MODE_ORDER:
        lines.append(
            f"| {mode} | {f2(modes[mode]['cpu_median'])} | {f2(modes[mode]['ram_mb_median'])} |"
        )

    lines.append("")
    lines.append("## Delta summary")
    lines.append("")
    lines.append("| Comparison | CPU delta (%) | RAM delta (MB) |")
    lines.append("|---|---:|---:|")
    for name, values in deltas.items():
        lines.append(
            f"| {name} | {f2(values.get('cpu_median_delta'))} | {f2(values.get('ram_mb_median_delta'))} |"
        )

    if tracing_components:
        lines.append("")
        lines.append("## Tracing/monitoring component medians")
        lines.append("")
        lines.append("| Mode | App CPU | App RAM | Tracing CPU | Tracing RAM |")
        lines.append("|---|---:|---:|---:|---:|")
        for mode in ["tracing_info", "tracing_debug"]:
            if mode not in tracing_components:
                continue
            comp = tracing_components[mode]
            lines.append(
                "| "
                + mode
                + " | "
                + f2(comp["app"]["cpu_median"])
                + " | "
                + f2(comp["app"]["ram_mb_median"])
                + " | "
                + f2(comp["tracing_monitoring"]["cpu_median"])
                + " | "
                + f2(comp["tracing_monitoring"]["ram_mb_median"])
                + " |"
            )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Lab5 comparison report from benchmark artifacts")
    parser.add_argument("--results-dir", default="results", help="Path to benchmark results directory")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    modes, tracing_components = build_mode_summary(results_dir)
    deltas = build_deltas(modes)

    report = {
        "modes": modes,
        "deltas": deltas,
        "tracing_components": tracing_components,
    }

    json_path = results_dir / "lab5_comparison_report.json"
    md_path = results_dir / "lab5_comparison_report.md"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, modes, deltas, tracing_components)

    print(f"Generated: {json_path}")
    print(f"Generated: {md_path}")


if __name__ == "__main__":
    main()
