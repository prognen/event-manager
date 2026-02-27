#!/bin/bash
# Сбор метрик ресурсов (CPU, RAM) во время бенчмарка.
# Запускается в фоне на время прогона, пишет в OUTPUT_FILE.
# Использование: ./collect_stats.sh CONTAINER_NAME OUTPUT_FILE DURATION_SEC

CONTAINER="${1:-test_debug-app-1}"
OUTPUT_FILE="${2:-results/resources.csv}"
DURATION_SEC="${3:-300}"

mkdir -p "$(dirname "$OUTPUT_FILE")"
echo "timestamp,container,cpu_percent,mem_usage,mem_percent" > "$OUTPUT_FILE"

END_TIME=$(($(date +%s) + DURATION_SEC))
while [ "$(date +%s)" -lt "$END_TIME" ]; do
  docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" "$CONTAINER" 2>/dev/null | while read -r line; do
    echo "$(date -Iseconds),$line" >> "$OUTPUT_FILE"
  done
  sleep 5
done

echo "Collected stats to $OUTPUT_FILE"
