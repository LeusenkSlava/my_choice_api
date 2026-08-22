#!/bin/bash
set -e

BOOTSTRAP="kafka:9092"

# формат: topic:partitions:replication:retention_ms
TOPICS=(
  "tickets.created:3:1:604800000"
  "tickets.paid:3:1:604800000"
  "notifications.email:3:1:259200000"
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