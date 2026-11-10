from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from backend.app.models.alert import Alert
from backend.app.models.transaction import Transaction
from backend.app.models.case import Case, case_alerts
from backend.app.models.analyst import Analyst
from backend.app.models.analyst_action import AnalystAction
from backend.app.models.case_event import CaseEvent


# Group alerts from the same account within this time window.
GROUPING_WINDOW_HOURS = 24


def get_next_id(db, model, field_name, prefix):
    """
    Generate the next sequential ID without reusing existing IDs.
    Example: CASE-2026-000001
    """
    column = getattr(model, field_name)
    existing_ids = db.query(column).all()

    highest_number = 0

    for row in existing_ids:
        value = row[0]

        if value and value.startswith(prefix):
            try:
                number = int(value.split("-")[-1])
                highest_number = max(highest_number, number)
            except ValueError:
                continue

    return f"{prefix}{highest_number + 1:06d}"


def seed_default_analysts(db):
    """
    Create synthetic analysts only if the analysts table is empty.
    These are demonstration records, not real employees.
    """
    existing_count = db.query(Analyst).count()

    if existing_count > 0:
        return

    analysts = []

    for number in range(1, 6):
        analysts.append(
            Analyst(
                analyst_id=f"ANL-{number:03d}",
                full_name=f"Risk Analyst {number:02d}",
                email=f"analyst{number:02d}@example.test",
                role="ANALYST",
                is_active=True,
            )
        )

    db.add_all(analysts)
    db.flush()


def get_least_loaded_analyst(db, workload):
    """
    Select the active analyst with the fewest open cases.
    Ties are resolved using analyst ID.
    """
    analysts = (
        db.query(Analyst)
        .filter(Analyst.is_active.is_(True))
        .order_by(Analyst.analyst_id)
        .all()
    )

    if not analysts:
        raise ValueError("No active analysts are available.")

    return min(
        analysts,
        key=lambda analyst: (
            workload.get(analyst.analyst_id, 0),
            analyst.analyst_id,
        ),
    )


def get_analyst_workload(db):
    """
    Count each analyst's currently open or in-progress cases.
    """
    results = (
        db.query(
            Case.assigned_analyst_id,
            func.count(Case.case_id),
        )
        .filter(
            Case.case_status.in_(["OPEN", "IN_PROGRESS"]),
            Case.assigned_analyst_id.isnot(None),
        )
        .group_by(Case.assigned_analyst_id)
        .all()
    )

    return {
        analyst_id: count
        for analyst_id, count in results
    }


def get_case_priority(alerts):
    """Determine case priority from the highest alert risk level."""

    priority_order = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }

    highest_alert = max(
        alerts,
        key=lambda alert: priority_order.get(
            alert.risk_level.upper(), 0
        )
    )

    return highest_alert.risk_level.upper()


def get_case_due_date(priority):
    """Set an investigation deadline based on case priority."""

    now = datetime.now(timezone.utc)

    deadlines = {
        "CRITICAL": 4,
        "HIGH": 12,
        "MEDIUM": 48,
        "LOW": 120,
    }

    hours = deadlines.get(priority, 48)

    return now + timedelta(hours=hours)


def group_alerts_by_account(alert_records):
    """
    Group alerts from the same account when their transaction
    timestamps are no more than 24 hours apart.
    """
    groups = []

    for record in alert_records:
        alert, transaction = record

        if not groups:
            groups.append({
                "account_id": transaction.account_id,
                "last_timestamp": transaction.transaction_timestamp,
                "alerts": [alert],
            })
            continue

        current_group = groups[-1]

        same_account = (
            current_group["account_id"] == transaction.account_id
        )

        within_window = (
            transaction.transaction_timestamp
            - current_group["last_timestamp"]
            <= timedelta(hours=GROUPING_WINDOW_HOURS)
        )

        if same_account and within_window:
            current_group["alerts"].append(alert)
            current_group["last_timestamp"] = (
                transaction.transaction_timestamp
            )
        else:
            groups.append({
                "account_id": transaction.account_id,
                "last_timestamp": transaction.transaction_timestamp,
                "alerts": [alert],
            })

    return groups


def create_cases(db):
    """
    Main case-generation workflow:

    1. Find alerts not already linked to a case.
    2. Group related alerts by account and time.
    3. Create cases.
    4. Assign analysts by workload.
    5. Record case events and analyst actions.
    """
    seed_default_analysts(db)

    # Find alerts that are not already associated with a case.
    existing_alert_ids = db.query(
        case_alerts.c.alert_id
    ).all()

    existing_alert_ids = {
        row[0] for row in existing_alert_ids
    }

    query = (
        db.query(Alert, Transaction)
        .join(
            Transaction,
            Alert.transaction_id == Transaction.transaction_id,
        )
        .order_by(
            Transaction.account_id,
            Transaction.transaction_timestamp,
            Alert.alert_id,
        )
    )

    if existing_alert_ids:
        query = query.filter(
            ~Alert.alert_id.in_(existing_alert_ids)
        )

    alert_records = query.all()

    if not alert_records:
        return {
            "message": "No new alerts are available for case creation.",
            "cases_created": 0,
        }

    grouped_alerts = group_alerts_by_account(alert_records)

    workload = get_analyst_workload(db)

    cases_created = 0

    try:
        for group in grouped_alerts:
            alerts = group["alerts"]
            account_id = group["account_id"]

            priority = get_case_priority(alerts)

            case_id = get_next_id(
                db,
                Case,
                "case_id",
                "CASE-2026-",
            )

            analyst = get_least_loaded_analyst(db, workload)

            new_case = Case(
                case_id=case_id,
                case_title=f"{priority} Risk Review - {account_id}",
                description=(
                    f"Investigation case containing {len(alerts)} "
                    f"related alert(s) for account {account_id}."
                ),
                priority=priority,
                case_status="OPEN",
                assigned_analyst_id=analyst.analyst_id,
                due_at=get_case_due_date(priority),
            )

            # Connect all alerts belonging to this case.
            new_case.alerts = alerts

            db.add(new_case)
            db.flush()

            # Record case creation.
            creation_event = CaseEvent(
                event_id=get_next_id(
                    db, CaseEvent, "event_id", "CEV-2026-"
                ),
                case_id=case_id,
                event_type="CASE_CREATED",
                previous_status=None,
                new_status="OPEN",
                description=f"Case created with {len(alerts)} alert(s).",
            )

            db.add(creation_event)
            db.flush()

            # Record analyst assignment as a separate event.
            assignment_event = CaseEvent(
                event_id=get_next_id(
                    db, CaseEvent, "event_id", "CEV-2026-"
                ),
                case_id=case_id,
                event_type="ANALYST_ASSIGNED",
                previous_status=None,
                new_status="OPEN",
                description=f"Assigned to analyst {analyst.analyst_id}.",
            )

            # Record assignment in analyst action history.
            assignment_action = AnalystAction(
                action_id=get_next_id(
                    db, AnalystAction, "action_id", "ACT-2026-"
                ),
                case_id=case_id,
                analyst_id=analyst.analyst_id,
                action_type="CASE_ASSIGNED",
                previous_status=None,
                new_status="OPEN",
                comments="Case automatically assigned by workload balancing.",
            )

            db.add_all([assignment_event, assignment_action])
            db.flush()

            workload[analyst.analyst_id] = (
                workload.get(analyst.analyst_id, 0) + 1
            )

            cases_created += 1

        db.commit()

        return {
            "message": "Cases created and analysts assigned successfully.",
            "cases_created": cases_created,
            "alerts_processed": len(alert_records),
        }

    except Exception:
        db.rollback()
        raise
