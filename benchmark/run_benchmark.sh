#!/bin/bash
# Бенчмарк производительности (Лабораторная №3, №5)
#
# Лаба 3: сравнение FastAPI vs Flask
# Лаба 5: сравнение приложение vs трассировка/мониторинг/логирование
#
# Режимы из modes.json:
#   no_tracing_info   - без трассировки, info-логи (базовый)
#   tracing_info      - с OpenTelemetry, info-логи
#   no_tracing_debug  - без трассировки, debug-логи (нагрузка от логирования)
#   tracing_debug     - трассировка + debug-логи
#   flask             - альтернативный фреймворк
#
# Использование:
#   ./benchmark/run_benchmark.sh [mode_name]   # один режим
#   ./benchmark/run_benchmark.sh all           # все режимы
#   ./benchmark/run_benchmark.sh fastapi       # = no_tracing_info
#   BENCHMARK_QUICK=1 ./benchmark/run_benchmark.sh tracing_info  # 60 сек
set -e

DURATION="${BENCHMARK_DURATION:-300}"
QUICK="${BENCHMARK_QUICK:-}"
OUTPUT_DIR="${BENCHMARK_OUTPUT:-results}"
MODES_FILE="./benchmark/modes.json"
# Лаба 3 п.2: BENCHMARK_FRESH_BUILD=1 — полная пересборка образа без кэша (медленно)
FRESH_BUILD="${BENCHMARK_FRESH_BUILD:-0}"

mkdir -p "$OUTPUT_DIR"

run_mode() {
    local name=$1
    local framework=$2
    local enable_tracing=${3:-0}
    local log_level=${4:-info}
    local profiles=$5
    local app_url="http://localhost:8000"
    local app_port=8000

    echo ""
    echo "=========================================="
    echo "==> Benchmark: $name (tracing=$enable_tracing, log=$log_level)"
    echo "=========================================="

    if [ "$framework" = "flask" ]; then
        app_url="http://localhost:8001"
        app_port=8001
        # Лаба 3 п.2: отдельный докер-образ на каждый прогон — build + force-recreate
        [ "$FRESH_BUILD" = "1" ] && BUILD_OPTS="--no-cache" || BUILD_OPTS=""
        docker compose --profile benchmark-flask build $BUILD_OPTS flask-app
        docker compose --profile benchmark-flask up -d --force-recreate flask-app 2>/dev/null || true
        sleep 5
    else
        # FastAPI: Лаба 3 п.2 — отдельный образ на прогон: build + force-recreate
        docker compose stop app otel-collector jaeger 2>/dev/null || true
        [ "$FRESH_BUILD" = "1" ] && BUILD_OPTS="--no-cache" || BUILD_OPTS=""
        docker compose build $BUILD_OPTS app
        PROFILE_ARGS=""
        for p in $profiles; do PROFILE_ARGS="$PROFILE_ARGS --profile $p"; done
        if [ "$enable_tracing" = "1" ]; then
            ENABLE_TRACING=$enable_tracing LOG_LEVEL=$log_level \
                docker compose $PROFILE_ARGS up -d --force-recreate db app otel-collector jaeger 2>/dev/null || true
        else
            ENABLE_TRACING=$enable_tracing LOG_LEVEL=$log_level \
                docker compose $PROFILE_ARGS up -d --force-recreate db app 2>/dev/null || true
        fi
        [ "$enable_tracing" = "1" ] && sleep 20 || sleep 15
    fi

    echo "Waiting for app at $app_url..."
    for i in $(seq 1 30); do
        if curl -sf "$app_url/health" >/dev/null 2>&1; then
            echo "App is ready."
            break
        fi
        sleep 2
    done
    if ! curl -sf "$app_url/health" >/dev/null 2>&1; then
        echo "ERROR: App not responding at $app_url"
        return 1
    fi

    # Сбор метрик ресурсов (app + otel + jaeger при трассировке)
    CONTAINER_NAME="${DOCKER_APP_CONTAINER:-test_debug-app-1}"
    if [ "$framework" = "fastapi" ]; then
        CONTAINER_NAME="test_debug-app-1"
    else
        CONTAINER_NAME="flask_app"
    fi

    if command -v docker >/dev/null 2>&1; then
        ./benchmark/collect_stats.sh "$CONTAINER_NAME" "$OUTPUT_DIR/${name}_resources.csv" "$DURATION" &
        STATS_PID=$!
        if [ "$enable_tracing" = "1" ] && docker ps -q -f name=otel_collector 2>/dev/null | grep -q .; then
            ./benchmark/collect_stats_multi.sh "$OUTPUT_DIR/${name}_resources_full.csv" "$DURATION" \
                "test_debug-app-1" "otel_collector" "jaeger" &
            STATS_FULL_PID=$!
        fi
    fi

    EXTRA_ARGS=""
    [ -n "$QUICK" ] && EXTRA_ARGS="$EXTRA_ARGS --quick"
    [ -n "${BENCHMARK_SCENARIO:-}" ] && EXTRA_ARGS="$EXTRA_ARGS --scenario $BENCHMARK_SCENARIO"
    python benchmark/benchmark_runner.py \
        --base-url "$app_url" \
        --duration "$DURATION" \
        --output-dir "$OUTPUT_DIR" \
        --framework "$framework" \
        $EXTRA_ARGS

    [ -n "${STATS_PID:-}" ] && wait $STATS_PID 2>/dev/null || true
    [ -n "${STATS_FULL_PID:-}" ] && wait $STATS_FULL_PID 2>/dev/null || true

    if [ -f "$OUTPUT_DIR/${name}_resources.csv" ]; then
        python benchmark/aggregate_resources.py \
            "$OUTPUT_DIR/${name}_resources.csv" \
            "$OUTPUT_DIR/${name}_resources_report.json"
    fi
    if [ -f "$OUTPUT_DIR/${name}_resources_full.csv" ]; then
        python benchmark/aggregate_resources.py \
            "$OUTPUT_DIR/${name}_resources_full.csv" \
            "$OUTPUT_DIR/${name}_resources_full_report.json" \
            --multi
    fi

    echo "Saved: $OUTPUT_DIR/${name}_*"
}

# Парсинг modes.json (требует jq)
get_mode() {
    local name=$1
    jq -r --arg n "$name" '
        .[] | select(.name == $n) |
        "\(.framework)|\(.ENABLE_TRACING // "0")|\(.LOG_LEVEL // "info")|\(.profiles | join(" "))"
    ' "$MODES_FILE" 2>/dev/null | head -1
}

MODE=${1:-fastapi}

if [ "$MODE" = "all" ]; then
    for m in $(jq -r '.[].name' "$MODES_FILE" 2>/dev/null); do
        run_mode "$m" $(get_mode "$m")
    done
elif [ "$MODE" = "fastapi" ]; then
    run_mode "no_tracing_info" "fastapi" "0" "info" "benchmark"
elif [ "$MODE" = "flask" ]; then
    run_mode "flask" "flask" "0" "info" "benchmark-flask"
else
    # Режим по имени из modes.json
    line=$(get_mode "$MODE")
    if [ -z "$line" ]; then
        echo "Unknown mode: $MODE"
        echo "Available: $(jq -r '.[].name' $MODES_FILE 2>/dev/null | tr '\n' ' ')"
        exit 1
    fi
    IFS='|' read -r framework tracing log_level profiles <<< "$line"
    run_mode "$MODE" "$framework" "$tracing" "$log_level" "$profiles"
fi

echo ""
echo "=== Benchmark completed ==="
