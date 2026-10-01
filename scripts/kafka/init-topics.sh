#!/bin/bash
set -e

BOOTSTRAP="kafka:9092"

# формат: topic:partitions:replication:retention_ms
TOPICS=(
  "ai_plot.novel.generate:3:1:604800000"
  "generation.results:3:1:604800000"
)

for entry in "${TOPICS[@]}"; do
  IFS=':' read -r name partitions replication retention <<< "$entry"

  echo "Creating topic: $name"
  /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server "$BOOTSTRAP" \
    --create --if-not-exists \
    --topic "$name" \
    --partitions "$partitions" \
    --replication-factor "$replication"

  /opt/kafka/bin/kafka-configs.sh \
    --bootstrap-server "$BOOTSTRAP" \
    --entity-type topics --entity-name "$name" \
    --alter --add-config "retention.ms=$retention"
done

echo "All topics configured."