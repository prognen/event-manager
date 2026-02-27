#!/usr/bin/env python3
"""
Бенчмарк производительности web-фреймворка (Лабораторная №3).

Сценарии:
1. JSON-сериализация (/api/benchmark/json)
2. Средний запрос с БД и шаблоном (/venue.html)
3. Тяжёлый запрос (/event.html)
4. Одновременный логин (concurrent /api/login)

Запуск: 5-10 минут нагрузки, сбор перцентилей, CSV, JSON-отчёт.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Установите httpx: pip install httpx", file=sys.stderr)
    sys.exit(1)

PERCENTILES = (0.5, 0.75, 0.9, 0.95, 0.99)
DEFAULT_DURATION_SEC = 300  # 5 минут
DEFAULT_CONCURRENCY = 10


def percentile(sorted_data: list[float], p: float) -> float:
    """Вычисление перцентиля (линейная интерполяция)."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * p
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def compute_stats(latencies_ms: list[float]) -> dict[str, float]:
    """Статистика по задержкам: min, max, mean, перцентили."""
    if not latencies_ms:
        return {"count": 0, "min": 0, "max": 0, "mean": 0}
    sorted_lat = sorted(latencies_ms)
    result: dict[str, float] = {
        "count": len(sorted_lat),
        "min": min(sorted_lat),
        "max": max(sorted_lat),
        "mean": sum(sorted_lat) / len(sorted_lat),
    }
    for p in PERCENTILES:
        result[f"p{int(p*100)}"] = percentile(sorted_lat, p)
    return result


def build_histogram(latencies_ms: list[float], bins: int = 20) -> list[dict[str, float]]:
    """Гистограмма распределения."""
    if not latencies_ms:
        return []
    sorted_lat = sorted(latencies_ms)
    lo, hi = sorted_lat[0], sorted_lat[-1]
    if hi == lo:
        return [{"bin_start": lo, "bin_end": hi, "count": len(sorted_lat)}]
    step = (hi - lo) / bins or 1
    hist: list[dict[str, float]] = []
    for i in range(bins):
        b_start = lo + i * step
        b_end = lo + (i + 1) * step
        count = sum(1 for x in sorted_lat if b_start <= x < b_end)
        if i == bins - 1:
            count += sum(1 for x in sorted_lat if x == b_end)
        hist.append({"bin_start": b_start, "bin_end": b_end, "count": count})
    return hist


async def run_scenario(
    client: httpx.AsyncClient,
    name: str,
    method: str,
    url: str,
    duration_sec: float,
    concurrency: int,
    **kwargs: object,
) -> tuple[list[float], list[tuple[float, float]]]:
    """
    Запуск сценария на заданное время.
    Возвращает: (latencies_ms, time_series [(timestamp, latency_ms)])
    """
    latencies: list[float] = []
    time_series: list[tuple[float, float]] = []
    start_time = time.perf_counter()
    request_count = 0

    async def worker() -> None:
        nonlocal latencies, time_series, request_count
        while time.perf_counter() - start_time < duration_sec:
            t0 = time.perf_counter()
            try:
                if method.upper() == "GET":
                    r = await client.get(url, **kwargs)
                else:
                    r = await client.post(url, **kwargs)
                if r.status_code == 200:
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    latencies.append(elapsed_ms)
                    time_series.append((t0 - start_time, elapsed_ms))
                    request_count += 1
            except Exception:
                pass
            await asyncio.sleep(0)

    workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
    await asyncio.gather(*workers)
    return latencies, time_series


# user1 из db-init, пароль 123!e5T78
BENCHMARK_LOGIN = "user1"
BENCHMARK_PASSWORD = "123!e5T78"


async def run_login_scenario(
    base_url: str,
    duration_sec: float,
    concurrency: int,
    login: str,
    password: str,
) -> tuple[list[float], list[tuple[float, float]]]:
    """Сценарий одновременного логина (использует созданного пользователя)."""
    latencies: list[float] = []
    time_series: list[tuple[float, float]] = []
    start_time = time.perf_counter()

    async def login_worker() -> None:
        nonlocal latencies, time_series
        async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as c:
            while time.perf_counter() - start_time < duration_sec:
                t0 = time.perf_counter()
                try:
                    r = await c.post(
                        "/api/login",
                        json={"login": login, "password": password},
                    )
                    if r.status_code == 200:
                        elapsed_ms = (time.perf_counter() - t0) * 1000
                        latencies.append(elapsed_ms)
                        time_series.append((t0 - start_time, elapsed_ms))
                except Exception:
                    pass
                await asyncio.sleep(0.1)

    workers = [asyncio.create_task(login_worker()) for _ in range(concurrency)]
    await asyncio.gather(*workers)
    return latencies, time_series


async def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark web framework")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_SEC)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--output-dir", default="results", help="Output directory")
    parser.add_argument("--framework", default="fastapi", help="fastapi | flask")
    parser.add_argument("--quick", action="store_true", help="Быстрый прогон (60 сек)")
    parser.add_argument(
        "--scenario",
        choices=["json", "medium", "heavy", "login", "all"],
        default="all",
        help="Запустить только указанный сценарий (по умолчанию — все)",
    )
    args = parser.parse_args()

    duration = 60 if args.quick else args.duration
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    framework = args.framework
    prefix = f"{framework}_{int(time.time())}"

    print(f"Benchmark: {framework}, duration={duration}s, concurrency={args.concurrency}")
    print("=" * 60)

    all_results: dict[str, dict] = {}
    all_latencies: dict[str, list[float]] = {}
    all_time_series: dict[str, list[tuple[float, float]]] = {}

    # Оба фреймворка используют одни и те же benchmark-эндпоинты для честного сравнения
    medium_url, heavy_url = "/api/benchmark/medium", "/api/benchmark/heavy"

    async with httpx.AsyncClient(base_url=args.base_url, timeout=30.0) as client:
        if args.scenario in ("all", "json"):
            print("Scenario 1: JSON serialization (/api/benchmark/json)...")
            lat, ts = await run_scenario(
                client, "json", "GET", "/api/benchmark/json", duration, args.concurrency
            )
            all_latencies["json_serialization"] = lat
            all_time_series["json_serialization"] = ts
            all_results["json_serialization"] = compute_stats(lat)
            print(f"  Requests: {len(lat)}, p99: {all_results['json_serialization'].get('p99', 0):.2f} ms")

        if args.scenario in ("all", "medium"):
            print(f"Scenario 2: Medium request ({medium_url})...")
            lat, ts = await run_scenario(
                client, "medium", "GET", medium_url, duration, args.concurrency
            )
            all_latencies["medium_request"] = lat
            all_time_series["medium_request"] = ts
            all_results["medium_request"] = compute_stats(lat)
            print(f"  Requests: {len(lat)}, p99: {all_results['medium_request'].get('p99', 0):.2f} ms")

        if args.scenario in ("all", "heavy"):
            print(f"Scenario 3: Heavy request ({heavy_url})...")
            lat, ts = await run_scenario(
                client, "heavy", "GET", heavy_url, duration, args.concurrency
            )
            all_latencies["heavy_request"] = lat
            all_time_series["heavy_request"] = ts
            all_results["heavy_request"] = compute_stats(lat)
            print(f"  Requests: {len(lat)}, p99: {all_results['heavy_request'].get('p99', 0):.2f} ms")

        if args.scenario in ("all", "login"):
            print("Scenario 4: Concurrent login (/api/login)...")
            lat, ts = await run_login_scenario(
                args.base_url, duration, args.concurrency,
                BENCHMARK_LOGIN, BENCHMARK_PASSWORD,
            )
            all_latencies["concurrent_login"] = lat
            all_time_series["concurrent_login"] = ts
            all_results["concurrent_login"] = compute_stats(lat)
            print(f"  Requests: {len(lat)}, p99: {all_results['concurrent_login'].get('p99', 0):.2f} ms")

    # --- CSV ---
    csv_path = out_dir / f"{prefix}_latencies.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("scenario,request_id,timestamp_sec,latency_ms\n")
        for scenario, ts_data in all_time_series.items():
            for i, (t, lat_ms) in enumerate(ts_data):
                f.write(f"{scenario},{i},{t:.3f},{lat_ms:.3f}\n")
    print(f"\nCSV: {csv_path}")

    # --- JSON report ---
    report: dict = {
        "framework": framework,
        "duration_sec": duration,
        "concurrency": args.concurrency,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scenarios": {},
        "percentiles": list(PERCENTILES),
    }
    for name, stats in all_results.items():
        report["scenarios"][name] = {
            "statistics": stats,
            "histogram": build_histogram(all_latencies[name]),
            "time_series_sample": all_time_series[name][:: max(1, len(all_time_series[name]) // 100)],
        }
    json_path = out_dir / f"{prefix}_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"JSON report: {json_path}")

    # --- Resource summary placeholder (заполняется collect_stats) ---
    resources_path = out_dir / f"{prefix}_resources.json"
    resources = {
        "framework": framework,
        "components": {
            "app": {"cpu_min": 0, "cpu_max": 0, "cpu_median": 0, "ram_min_mb": 0, "ram_max_mb": 0, "ram_median_mb": 0},
        },
    }
    with open(resources_path, "w", encoding="utf-8") as f:
        json.dump(resources, f, indent=2)
    print(f"Resources (template): {resources_path}")

    print("\n=== Benchmark completed ===")


if __name__ == "__main__":
    asyncio.run(main())
