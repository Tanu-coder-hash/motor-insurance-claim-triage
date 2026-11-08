import time
import uuid
from datetime import datetime, timezone

from services.api.app.celery_app import celery_app
from services.api.app.database import SessionLocal
from services.api.app.models import Run, RunStep


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

        return {
            "run_id": run_id,
            "status": "completed",
        }

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