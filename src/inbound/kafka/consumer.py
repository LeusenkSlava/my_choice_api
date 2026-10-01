from aiokafka import AIOKafkaConsumer

from src.inbound.kafka.handlers import TOPIC_HANDLERS
from src.main.config.settings import settings

consumer = AIOKafkaConsumer(
    *TOPIC_HANDLERS.keys(),
    bootstrap_servers=settings.kafka.BOOTSTRAP_SERVERS,
    group_id="my-choice-api",
    enable_auto_commit=False,
)
