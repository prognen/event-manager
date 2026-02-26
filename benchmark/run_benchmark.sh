#!/bin/bash
set -e

MODES_FILE="./benchmark/modes.json"
MODES=$(jq -c '.[]' $MODES_FILE)

for mode in $MODES; do
    NAME=$(echo $mode | jq -r '.name')
    TRACING=$(echo $mode | jq -r '.ENABLE_TRACING')
    LOG_LEVEL=$(echo $mode | jq -r '.LOG_LEVEL')
    PROFILES=$(echo $mode | jq -r '.profiles | join(" --profile ")')

    echo "==> Running mode: $NAME"
    docker compose down -v --remove-orphans

    docker network inspect my_network >/dev/null 2>&1 || docker network create --driver bridge my_network
    docker network inspect monitoring >/dev/null 2>&1 || docker network create --driver bridge monitoring

    ENABLE_TRACING=$TRACING LOG_LEVEL=$LOG_LEVEL docker compose --profile $PROFILES up -d --remove-orphans

    sleep 5

    E2E_CONTAINER=$(docker compose --profile test run -d \
    -e ENABLE_TRACING=$TRACING \
    -e LOG_LEVEL=$LOG_LEVEL \
    -e OTEL_SERVICE_NAME=e2e-tests \
    e2e-tests)

    sleep 5

    ./benchmark/collect_stats.sh "$E2E_CONTAINER" "results/${NAME}.csv"
    docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" \
    test_debug-app-1 \
    jaeger \
    otel_collector \
    >> "results/${NAME}.csv"

    docker wait $E2E_CONTAINER
    docker rm $E2E_CONTAINER >/dev/null

    echo "Saved: results/${NAME}.csv"
done

echo "=== All benchmarks completed ==="
