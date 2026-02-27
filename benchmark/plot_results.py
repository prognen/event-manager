#!/usr/bin/env python3
"""Построение графиков по результатам бенчмарка (Лабораторная №3)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def load_report(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def plot_time_series(ts_data: list[tuple[float, float]], out_path: Path, title: str) -> None:
    if not ts_data:
        return
    times = [t for t, _ in ts_data]
    latencies = [lat for _, lat in ts_data]
    plt.figure(figsize=(10, 4))
    plt.plot(times, latencies, alpha=0.7)
    plt.xlabel("Время, сек")
    plt.ylabel("Задержка, мс")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=100)
    plt.close()


def plot_histogram(latencies: list[float], out_path: Path, title: str) -> None:
    if not latencies:
        return
    plt.figure(figsize=(8, 4))
    plt.hist(latencies, bins=30, edgecolor="black", alpha=0.7)
    plt.xlabel("Задержка, мс")
    plt.ylabel("Количество запросов")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=100)
    plt.close()


def plot_percentiles(stats: dict, out_path: Path, title: str) -> None:
    percentiles = ["p50", "p75", "p90", "p95", "p99"]
    labels = ["50%", "75%", "90%", "95%", "99%"]
    values = [stats.get(p, 0) for p in percentiles]
    plt.figure(figsize=(8, 4))
    plt.bar(labels, values, color="steelblue", edgecolor="black")
    plt.xlabel("Перцентиль")
    plt.ylabel("Задержка, мс")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=100)
    plt.close()


def main() -> None:
    if not HAS_MATPLOTLIB:
        print("Установите matplotlib для построения графиков: pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    # Последний аргумент — выходная папка (glob может раскрыться в несколько файлов)
    args = sys.argv[1:]
    if args and not str(args[-1]).endswith(".json"):
        out_dir = Path(args[-1])
        report_glob = args[0] if len(args) > 1 else "results/*_report.json"
    else:
        out_dir = Path("results/plots")
        report_glob = args[0] if args else "results/*_report.json"

    paths = list(Path(".").glob(report_glob))
    if not paths:
        paths = list(Path("results").glob("*_report.json"))
    if not paths:
        print("Не найден отчёт. Укажите путь: python plot_results.py results/fastapi_123_report.json")
        sys.exit(1)

    report_path = paths[0]
    report = load_report(report_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    framework = report.get("framework", "unknown")

    for scenario, data in report.get("scenarios", {}).items():
        stats = data.get("statistics", {})
        ts_sample = data.get("time_series_sample", [])
        # Восстанавливаем latencies из histogram или time_series
        latencies = []
        for _, lat in ts_sample:
            latencies.append(lat)
        if not latencies and "histogram" in data:
            for bin_data in data["histogram"]:
                cnt = int(bin_data.get("count", 0))
                mid = (bin_data.get("bin_start", 0) + bin_data.get("bin_end", 0)) / 2
                latencies.extend([mid] * cnt)

        prefix = f"{framework}_{scenario}"
        if ts_sample:
            plot_time_series(ts_sample, out_dir / f"{prefix}_time_series.png", f"{scenario} — задержка во времени")
        if latencies:
            plot_histogram(latencies, out_dir / f"{prefix}_histogram.png", f"{scenario} — гистограмма")
        if stats:
            plot_percentiles(stats, out_dir / f"{prefix}_percentiles.png", f"{scenario} — перцентили")

    print(f"Графики сохранены в {out_dir}")


if __name__ == "__main__":
    main()
