#!/bin/bash

CONTAINERS=$1
OUTPUT_FILE=$2

echo "container,cpu,mem" > $OUTPUT_FILE

for c in $CONTAINERS; do
    stats=$(docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" $c)
    echo "$stats" >> $OUTPUT_FILE
done
