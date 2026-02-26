#!/usr/bin/env python3
import os
import subprocess
import time
import psutil
from tabulate import tabulate

TEST_MODES = {
    "sequential": [
        "pytest",
        "tests/service_mock/",
        "-m",
        "unit",
        "-v",
        "-n",
        "0",
        "--capture=no",
    ],
    "parallel": [
        "pytest",
        "tests/service_mock/",
        "-m",
        "unit",
        "-v",
        "-n",
        "auto",
        "--capture=no",
    ],
    "by-class": [
        "pytest",
        "tests/service_mock/",
        "-m",
        "unit",
        "-v",
        "-n",
        "auto",
        "--dist=loadscope",
        "--capture=no",
    ],
    "by-file": [
        "pytest",
        "tests/service_mock/",
        "-m",
        "unit",
        "-v",
        "-n",
        "auto",
        "--dist=loadfile",
        "--capture=no",
    ],
}


def run_tests_and_collect_pids(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    start_time = time.time()
    observed_pids = set()

    while process.poll() is None:
        try:
            main_proc = psutil.Process(process.pid)
            observed_pids.add(main_proc.pid)
            for child in main_proc.children(recursive=True):
                observed_pids.add(child.pid)
        except psutil.NoSuchProcess:
            pass
        time.sleep(0.1)

    duration = time.time() - start_time
    stdout, stderr = process.communicate()
    return (
        duration,
        len(observed_pids),
        process.returncode,
        stdout.decode(),
        stderr.decode(),
    )


def main():
    print(f"=== Доступно ядер CPU: {os.cpu_count()} ===\n")
    results = []

    for mode, cmd in TEST_MODES.items():
        print(f"=== Запуск режима: {mode} ===")
        duration, unique_pids, returncode, stdout, stderr = run_tests_and_collect_pids(
            cmd
        )
        results.append(
            {
                "mode": mode,
                "time": f"{duration:.2f}",
                "pids": unique_pids,
                "returncode": returncode,
            }
        )

    table = [[r["mode"], r["time"], r["pids"], r["returncode"]] for r in results]
    print("\n=== Сравнительная таблица ===")
    print(
        tabulate(
            table,
            headers=["Режим", "Время (сек)", "Уникальные процессы", "Выходной код"],
            tablefmt="grid",
        )
    )


if __name__ == "__main__":
    main()
