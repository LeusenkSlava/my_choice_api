from aiokafka import AIOKafkaConsumer

from src.main.config.settings import settings

consumer = AIOKafkaConsumer(
    "my-choice-topic",
    bootstrap_servers=settings.kafka.BOOTSTRAP_SERVERS,
    group_id="my-choice-api",
)
