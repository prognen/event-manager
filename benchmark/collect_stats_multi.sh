#!/bin/bash
# Сбор метрик для нескольких контейнеров (app + otel + jaeger для Лабы 5).
# Использование: ./collect_stats_multi.sh OUTPUT_FILE DURATION_SEC CONTAINER1 CONTAINER2 ...
OUTPUT_FILE="${1:-results/resources_full.csv}"
DURATION_SEC="${2:-300}"
shift 2
CONTAINERS=("$@")

mkdir -p "$(dirname "$OUTPUT_FILE")"
echo "timestamp,container,cpu_percent,mem_usage" > "$OUTPUT_FILE"

END_TIME=$(($(date +%s) + DURATION_SEC))
while [ "$(date +%s)" -lt "$END_TIME" ]; do
  for c in "${CONTAINERS[@]}"; do
    docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" "$c" 2>/dev/null | while read -r line; do
      echo "$(date -Iseconds),$line" >> "$OUTPUT_FILE"
    done
  done
  sleep 5
done

echo "Collected multi stats to $OUTPUT_FILE"
