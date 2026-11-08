from celery import Celery

from services.api.app.config import settings


# Create the Celery application.
celery_app = Celery(
    "motor_insurance",
    broker=settings.redis_url,
    include=[
        "services.intake_agent.tasks",
    ],
)


# Configure background task processing.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Do not store task results in Redis.
    # PostgreSQL will store claim processing results.
    task_ignore_result=True,

    # Acknowledge tasks only after successful execution.
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Process one task at a time per worker.
    worker_prefetch_multiplier=1,

    # Redis visibility timeout.
    broker_transport_options={
        "visibility_timeout": 3600,
    },

    # Route tasks to their respective queues.
    task_routes={
        "intake.*": {"queue": "intake"},
        "coverage.*": {"queue": "coverage"},
    },
)