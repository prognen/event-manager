#!/usr/bin/env python3
"""Агрегация метрик ресурсов из CSV в JSON (min/max/median)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def parse_mem(mem_str: str) -> float:
    """Парсинг '100MiB / 2GiB' -> MB."""
    m = re.search(r"([\d.]+)\s*([KMGT]?i?B)", mem_str.strip())
    if not m:
        return 0.0
    val = float(m.group(1))
    unit = m.group(2).upper()
    if "KIB" in unit or "KB" in unit:
        return val / 1024
    if "MIB" in unit or "MB" in unit:
        return val
    if "GIB" in unit or "GB" in unit:
        return val * 1024
    return val


def parse_cpu(cpu_str: str) -> float:
    """Парсинг '45.23%' -> 45.23."""
    return float(cpu_str.replace("%", "").strip() or 0)


def main() -> None:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "results/resources.csv"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "results/resources_report.json"
    multi_mode = "--multi" in sys.argv

    path = Path(csv_path)
    if not path.exists():
        print(f"File not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    def stats(vals: list[float]) -> dict[str, float]:
        if not vals:
            return {"min": 0, "max": 0, "median": 0}
        s = sorted(vals)
        n = len(s)
        return {
            "min": min(s),
            "max": max(s),
            "median": s[n // 2] if n else 0,
        }

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) < 2:
        print("No data in CSV", file=sys.stderr)
        sys.exit(1)

    if multi_mode:
        # Группировка по контейнеру (Лаба 5: app, otel, jaeger)
        by_container: dict[str, list[tuple[float, float]]] = {}
        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) >= 4:
                _ts, name, cpu, mem = parts[0], parts[1], parts[2], parts[3]
                try:
                    c_val = parse_cpu(cpu)
                    m_val = parse_mem(mem.split("/")[0].strip())
                    if name not in by_container:
                        by_container[name] = []
                    by_container[name].append((c_val, m_val))
                except (ValueError, IndexError):
                    pass
        report = {
            "components": {},
            "summary": {
                "app": {},
                "tracing_monitoring": {},
            },
        }
        app_cpu, app_mem = [], []
        tracing_cpu, tracing_mem = [], []
        for name, vals in by_container.items():
            cpus = [v[0] for v in vals]
            mems = [v[1] for v in vals]
            report["components"][name] = {
                "cpu": stats(cpus),
                "ram_mb": stats(mems),
                "samples": len(vals),
            }
            if "app" in name or "flask" in name:
                app_cpu.extend(cpus)
                app_mem.extend(mems)
            else:
                tracing_cpu.extend(cpus)
                tracing_mem.extend(mems)
        report["summary"]["app"] = {"cpu": stats(app_cpu), "ram_mb": stats(app_mem)}
        report["summary"]["tracing_monitoring"] = {"cpu": stats(tracing_cpu), "ram_mb": stats(tracing_mem)}
    else:
        cpu_vals: list[float] = []
        mem_vals: list[float] = []
        container_name = "app"
        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) >= 4:
                _ts, name, cpu, mem = parts[0], parts[1], parts[2], parts[3]
                container_name = name
                try:
                    cpu_vals.append(parse_cpu(cpu))
                    mem_vals.append(parse_mem(mem.split("/")[0].strip()))
                except (ValueError, IndexError):
                    pass
        report = {
            "component": container_name,
            "cpu": stats(cpu_vals),
            "ram_mb": stats(mem_vals),
            "samples": len(cpu_vals),
        }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Resources report: {out_path}")


if __name__ == "__main__":
    main()
