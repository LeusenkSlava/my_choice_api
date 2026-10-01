from src.inbound.kafka.tasks.consume_loop import consume_loop
from src.outbound.ai_plot.tasks.generation_job_relay_worker import (
    run_generation_job_relay_worker,
)

BACKGROUND_WORKERS = {
    "generation_job_relay": run_generation_job_relay_worker,
    "consume_loop": consume_loop,
}
