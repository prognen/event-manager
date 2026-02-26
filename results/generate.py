import pandas as pd


def parse_memory(mem_str):
    """Парсит использование памяти в MiB"""
    if "MiB" in mem_str:
        return float(mem_str.split("MiB")[0].strip())
    return 0.0


def parse_cpu(cpu_str):
    """Парсит использование CPU в %"""
    return float(cpu_str.replace("%", ""))


# Загружаем данные из всех файлов
files = {
    "no_tracing_default": "./results/no_tracing_default_logs.csv",
    "no_tracing_debug": "./results/no_tracing_debug_logs.csv",
    "tracing_default": "./results/tracing_default_logs.csv",
    "tracing_debug": "./results/tracing_debug_logs.csv",
}

data = {}
for config, filename in files.items():
    try:
        df = pd.read_csv(filename)
        data[config] = {}
        for _, row in df.iterrows():
            container = row["container"]
            data[config][container] = {
                "cpu": parse_cpu(row["cpu"]),
                "mem": parse_memory(row["mem"]),
            }
    except:
        print(f"Ошибка загрузки {filename}")
        continue

# Создаем txt отчет
with open("./results/report.txt", "w") as f:
    f.write("СРАВНЕНИЕ ПОТРЕБЛЕНИЯ РЕСУРСОВ\n")
    f.write("=" * 50 + "\n\n")

    # CPU таблица
    f.write("CPU (%):\n")
    f.write("-" * 71 + "\n")
    f.write(
        f"{'Контейнер':<35} {'no_def':<8} {'no_debug':<8} {'tr_def':<8} {'tr_debug':<8}\n"
    )
    f.write("-" * 71 + "\n")

    all_containers = set()
    for config_data in data.values():
        all_containers.update(config_data.keys())

    for container in sorted(all_containers):
        row = [container]
        for config in [
            "no_tracing_default",
            "no_tracing_debug",
            "tracing_default",
            "tracing_debug",
        ]:
            if config in data and container in data[config]:
                row.append(f"{data[config][container]['cpu']:.2f}")
            else:
                row.append("N/A")
        f.write(f"{row[0]:<35} {row[1]:<8} {row[2]:<8} {row[3]:<8} {row[4]:<8}\n")

    # Memory таблица
    f.write("\n\nПАМЯТЬ (MiB):\n")
    f.write("-" * 71 + "\n")
    f.write(
        f"{'Контейнер':<35} {'no_def':<8} {'no_debug':<8} {'tr_def':<8} {'tr_debug':<8}\n"
    )
    f.write("-" * 71 + "\n")

    for container in sorted(all_containers):
        row = [container]
        for config in [
            "no_tracing_default",
            "no_tracing_debug",
            "tracing_default",
            "tracing_debug",
        ]:
            if config in data and container in data[config]:
                row.append(f"{data[config][container]['mem']:.1f}")
            else:
                row.append("N/A")
        f.write(f"{row[0]:<35} {row[1]:<8} {row[2]:<8} {row[3]:<8} {row[4]:<8}\n")

print("✅ report.txt создан")
