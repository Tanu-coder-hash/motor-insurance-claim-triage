import time
import uuid
import hashlib
import json
import redis
from datetime import datetime, timezone

from services.api.app.celery_app import celery_app
from services.api.app.database import SessionLocal
from services.api.app.config import settings
from services.api.app.models import Run, RunStep

def save_claim_cache(fnol_data: dict, run_id: str, result: dict):
    """Save a successfully processed claim result in Redis."""

    normalized_data = json.dumps(
        fnol_data,
        sort_keys=True,
        separators=(",", ":"),
    )

    cache_input = f"{normalized_data}:prompt-v1:index-v1"
    cache_key = hashlib.sha256(
        cache_input.encode("utf-8")
    ).hexdigest()

    client = redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    try:
        cache_data = {
            "original_run_id": run_id,
            "result": result,
        }

        client.setex(
            f"run_cache:{cache_key}",
            settings.run_cache_ttl_s,
            json.dumps(cache_data),
        )
    finally:
        client.close()
@celery_app.task(name="intake.process_claim")
def process_claim(run_id: str):
    """Temporary worker that simulates claim processing."""

    db = SessionLocal()

    try:
        claim_id = uuid.UUID(run_id)

        # Find the submitted claim.
        run = db.get(Run, claim_id)

        if run is None:
            return {"error": "Claim run not found"}

        # Mark the claim as running.
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        # Step 1: Simulate FNOL processing.
        step1 = RunStep(
            run_id=claim_id,
            seq=1,
            step_name="fnol_validation",
            status="completed",
            input_data={"message": "FNOL received"},
            output_data={"message": "FNOL validation completed"},
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        db.add(step1)
        db.commit()

        # Simulate processing time.
        time.sleep(2)

        # Step 2: Simulate claim assessment.
        step2 = RunStep(
            run_id=claim_id,
            seq=2,
            step_name="claim_assessment",
            status="completed",
            input_data={"message": "Starting claim assessment"},
            output_data={"message": "Placeholder assessment completed"},
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        db.add(step2)

        # Store a temporary processing result.
        run.result = {
            "claim_summary": "Temporary placeholder assessment",
            "recommendation": "manual_review",
            "confidence": 0.0,
            "citations": [],
            "message": "Replace with actual agent results later",
        }

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

        if run.status in ("completed", "escalated"):
            save_claim_cache(
                run.fnol_data,
                str(run_id),
                run.result,
            )

        return {"run_id": run_id, "status": "completed"}
    except Exception:
        db.rollback()

        # Mark the claim as failed if processing fails.
        run = db.get(Run, uuid.UUID(run_id))

        if run is not None:
            run.status = "failed"
            run.error = "Temporary worker processing failed"
            run.completed_at = datetime.now(timezone.utc)
            db.commit()

        raise

    finally:
        db.close()