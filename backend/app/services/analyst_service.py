
from backend.app.models.case import Case
from backend.app.models.analyst import Analyst
from backend.app.models.analyst_action import AnalystAction
from backend.app.models.case_event import CaseEvent


def get_next_id(db, model, field_name, prefix):
    """Generate the next sequential ID."""

    existing_ids = db.query(getattr(model, field_name)).all()

    numbers = []

    for row in existing_ids:
        value = row[0]

        if value.startswith(prefix):
            try:
                numbers.append(int(value.replace(prefix, "")))
            except ValueError:
                continue

    next_number = max(numbers, default=0) + 1

    return f"{prefix}{next_number:06d}"


def get_assigned_case(db, case_id, analyst_id):
    """Verify that the case belongs to the active analyst."""

    analyst = db.query(Analyst).filter(
        Analyst.analyst_id == analyst_id,
        Analyst.is_active == True,
    ).first()

    if not analyst:
        raise ValueError("Active analyst not found.")

    case = db.query(Case).filter(
        Case.case_id == case_id,
        Case.assigned_analyst_id == analyst_id,
    ).first()

    if not case:
        raise ValueError("Case not found or not assigned to this analyst.")

    return case


def record_action(
    db,
    case,
    analyst_id,
    action_type,
    previous_status=None,
    new_status=None,
    comments=None,
):
    """Save an analyst action and its corresponding case event."""

    action = AnalystAction(
        action_id=get_next_id(
            db, AnalystAction, "action_id", "ACT-2026-"
        ),
        case_id=case.case_id,
        analyst_id=analyst_id,
        action_type=action_type,
        previous_status=previous_status,
        new_status=new_status,
        comments=comments,
    )

    db.add(action)

    if previous_status != new_status:
        event = CaseEvent(
            event_id=get_next_id(
                db, CaseEvent, "event_id", "CEV-2026-"
            ),
            case_id=case.case_id,
            event_type=action_type,
            previous_status=previous_status,
            new_status=new_status,
            description=comments,
        )

        db.add(event)


def start_case(db, case_id, analyst_id):
    """Move an assigned case into investigation."""

    try:
        case = get_assigned_case(db, case_id, analyst_id)

        if case.case_status != "OPEN":
            raise ValueError("Only OPEN cases can be started.")

        previous_status = case.case_status
        case.case_status = "IN_PROGRESS"

        record_action(
            db,
            case,
            analyst_id,
            "INVESTIGATION_STARTED",
            previous_status,
            case.case_status,
            "Analyst started investigating the case.",
        )

        db.commit()

        return {
            "message": "Investigation started successfully.",
            "case_id": case.case_id,
            "status": case.case_status,
        }

    except Exception:
        db.rollback()
        raise


def add_investigation_comment(
    db, case_id, analyst_id, comments
):
    """Add an investigation comment without changing case status."""

    try:
        case = get_assigned_case(db, case_id, analyst_id)

        if case.case_status not in ["OPEN", "IN_PROGRESS", "ESCALATED"]:
            raise ValueError("Comments cannot be added to this case.")

        if not comments or not comments.strip():
            raise ValueError("Comment cannot be empty.")

        record_action(
            db,
            case,
            analyst_id,
            "INVESTIGATION_COMMENT",
            case.case_status,
            case.case_status,
            comments.strip(),
        )

        db.commit()

        return {
            "message": "Investigation comment added successfully.",
            "case_id": case.case_id,
        }

    except Exception:
        db.rollback()
        raise


def resolve_case(
    db, case_id, analyst_id, resolution, comments
):
    """Resolve a case with an explicit analyst decision."""

    try:
        case = get_assigned_case(db, case_id, analyst_id)

        if case.case_status not in ["IN_PROGRESS", "ESCALATED"]:
            raise ValueError("Only investigated cases can be resolved.")

        allowed_resolutions = [
            "CONFIRMED_SUSPICIOUS",
            "FALSE_POSITIVE",
        ]

        if resolution not in allowed_resolutions:
            raise ValueError("Invalid resolution decision.")

        previous_status = case.case_status
        case.case_status = "RESOLVED"

        decision_comments = (
            f"Resolution: {resolution}. {comments or ''}".strip()
        )

        record_action(
            db,
            case,
            analyst_id,
            "CASE_RESOLVED",
            previous_status,
            case.case_status,
            decision_comments,
        )

        db.commit()

        return {
            "message": "Case resolved successfully.",
            "case_id": case.case_id,
            "resolution": resolution,
            "status": case.case_status,
        }

    except Exception:
        db.rollback()
        raise


def escalate_case(db, case_id, analyst_id, comments):
    """Escalate a case for additional investigation."""

    try:
        case = get_assigned_case(db, case_id, analyst_id)

        if case.case_status not in ["OPEN", "IN_PROGRESS"]:
            raise ValueError("This case cannot be escalated.")

        if not comments or not comments.strip():
            raise ValueError("Escalation reason is required.")

        previous_status = case.case_status
        case.case_status = "ESCALATED"

        record_action(
            db,
            case,
            analyst_id,
            "CASE_ESCALATED",
            previous_status,
            case.case_status,
            comments.strip(),
        )

        db.commit()

        return {
            "message": "Case escalated successfully.",
            "case_id": case.case_id,
            "status": case.case_status,
        }

    except Exception:
        db.rollback()
        raise
