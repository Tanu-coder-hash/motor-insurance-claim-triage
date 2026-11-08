import json
import uuid
from datetime import datetime, timezone

import redis
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from libs.common.logging import configure_logging, get_logger
from libs.common.correlation import (
    get_correlation_id,
    set_correlation_id,
)
from libs.common.metrics import HTTP_REQUESTS, FNOL_REJECTED, RUNS_STARTED

from services.api.app.config import settings
from services.api.app.database import engine, SessionLocal
from services.api.app.contracts import FNOLRequest
from services.api.app.models import Run, Quarantine
from services.api.app.celery_app import celery_app
from services.intake_agent.tasks import process_claim


configure_logging(settings.log_level)
logger = get_logger("api")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Motor Insurance Claim Triage API",
)

# Expose Prometheus metrics.
app.mount("/metrics", make_asgi_app())


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = (
        request.headers.get("X-Correlation-ID")
        or str(uuid.uuid4())
    )

    set_correlation_id(correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id

    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """Save invalid FNOL requests in quarantine without creating a run."""

    raw_request = await request.body()

    quarantine_id = uuid.uuid4()

    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    db = SessionLocal()

    try:
        quarantine = Quarantine(
            quarantine_id=quarantine_id,
            raw_request=raw_request.decode(
                "utf-8",
                errors="replace",
            ),
            validation_errors={"errors": errors},
        )

        db.add(quarantine)
        db.commit()

    finally:
        db.close()

    FNOL_REJECTED.labels(reason="validation").inc()

    return JSONResponse(
        status_code=422,
        content={
            "quarantine_id": str(quarantine_id),
            "errors": errors,
        },
    )


@app.get("/")
def root():
    return {
        "message": "Motor Insurance Claim Triage API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    database_status = "healthy"
    redis_status = "healthy"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        database_status = "unhealthy"

    try:
        client = redis.Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
        )
        client.ping()
        client.close()
    except redis.RedisError:
        redis_status = "unhealthy"

    overall_status = (
        "healthy"
        if database_status == "healthy"
        and redis_status == "healthy"
        else "unhealthy"
    )

    return {
        "status": overall_status,
        "service": "motor-insurance-claim-triage-api",
        "version": settings.app_version,
        "dependencies": {
            "postgresql": database_status,
            "redis": redis_status,
        },
    }


@app.post("/v1/fnol", status_code=202)
def submit_fnol(fnol: FNOLRequest):
    """Validate and submit a claim for background processing."""

    db = SessionLocal()

    try:
        run_id = uuid.uuid4()

        run = Run(
            run_id=run_id,
            status="queued",
            correlation_id=get_correlation_id(),
            fnol_data=fnol.model_dump(mode="json"),
        )

        db.add(run)
        db.commit()

        # Send the claim to the Celery intake queue.
        process_claim.delay(str(run_id))

        RUNS_STARTED.inc()

        logger.info(
            "fnol_submitted",
            run_id=str(run_id),
        )

        return {
            "run_id": str(run_id),
            "status": "queued",
            "status_url": f"/v1/runs/{run_id}",
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@app.get("/v1/runs/{run_id}")
def get_run(run_id: uuid.UUID):
    """Retrieve the current status and result of a claim."""

    db = SessionLocal()

    try:
        run = db.get(Run, run_id)

        if run is None:
            return JSONResponse(
                status_code=404,
                content={"error": "Claim run not found"},
            )

        return {
            "run_id": str(run.run_id),
            "status": run.status,
            "result": run.result,
            "error": run.error,
            "created_at": (
                run.created_at.isoformat()
                if run.created_at else None
            ),
            "started_at": (
                run.started_at.isoformat()
                if run.started_at else None
            ),
            "completed_at": (
                run.completed_at.isoformat()
                if run.completed_at else None
            ),
        }

    finally:
        db.close()


@app.get("/v1/runs/{run_id}/trace")
def get_run_trace(run_id: uuid.UUID):
    """Retrieve all processing steps for a claim."""

    db = SessionLocal()

    try:
        run = db.get(Run, run_id)

        if run is None:
            return JSONResponse(
                status_code=404,
                content={"error": "Claim run not found"},
            )

        rows = db.execute(
            text("""
                SELECT seq, step_name, status,
                       input_data, output_data,
                       started_at, completed_at
                FROM run_steps
                WHERE run_id = :run_id
                ORDER BY seq
            """),
            {"run_id": run_id},
        ).mappings().all()

        return {
            "run_id": str(run_id),
            "steps": [
                {
                    **dict(row),
                    "started_at": (
                        row["started_at"].isoformat()
                        if row["started_at"] else None
                    ),
                    "completed_at": (
                        row["completed_at"].isoformat()
                        if row["completed_at"] else None
                    ),
                }
                for row in rows
            ],
        }

    finally:
        db.close()


@app.get("/health/worker")
def worker_health():
    """Check whether Celery workers are responding."""

    try:
        inspector = celery_app.control.inspect(timeout=2)
        workers = inspector.ping() or {}

        return {
            "status": "healthy" if workers else "unavailable",
            "workers": list(workers.keys()),
        }

    except Exception:
        return {
            "status": "unavailable",
            "workers": [],
        }


logger.info("api_application_initialized")