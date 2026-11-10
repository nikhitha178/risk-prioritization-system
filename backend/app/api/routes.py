
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.alert import Alert
from backend.app.models.transaction import Transaction
from backend.app.models.case import Case
from backend.app.models.analyst import Analyst
from backend.app.services.analyst_service import (
    start_case,
    add_investigation_comment,
    resolve_case,
    escalate_case,
)

router = APIRouter(prefix="/api", tags=["Risk Management"])


# Request bodies

class AnalystRequest(BaseModel):
    analyst_id: str


class CommentRequest(BaseModel):
    analyst_id: str
    comments: str


class ResolveRequest(BaseModel):
    analyst_id: str
    resolution: str
    comments: str = ""


# Dashboard

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    total_alerts = db.query(func.count(Alert.alert_id)).scalar() or 0
    total_cases = db.query(func.count(Case.case_id)).scalar() or 0
    total_transactions = db.query(
        func.count(Transaction.transaction_id)
    ).scalar() or 0
    total_analysts = db.query(func.count(Analyst.analyst_id)).filter(
        Analyst.is_active == True
    ).scalar() or 0

    alert_levels = db.query(
        Alert.risk_level,
        func.count(Alert.alert_id)
    ).group_by(Alert.risk_level).all()

    case_priorities = db.query(
        Case.priority,
        func.count(Case.case_id)
    ).group_by(Case.priority).all()

    case_statuses = db.query(
        Case.case_status,
        func.count(Case.case_id)
    ).group_by(Case.case_status).all()

    return {
        "total_transactions": total_transactions,
        "total_alerts": total_alerts,
        "total_cases": total_cases,
        "active_analysts": total_analysts,
        "alert_risk_distribution": {
            level: count for level, count in alert_levels
        },
        "case_priority_distribution": {
            priority: count for priority, count in case_priorities
        },
        "case_status_distribution": {
            status: count for status, count in case_statuses
        },
    }


# Alerts

@router.get("/alerts")
def list_alerts(
    risk_level: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 500))

    query = db.query(Alert).join(
        Transaction,
        Alert.transaction_id == Transaction.transaction_id
    )

    if risk_level:
        query = query.filter(
            Alert.risk_level == risk_level.upper()
        )

    alerts = query.order_by(
        Alert.created_at.desc()
    ).limit(limit).all()

    results = []

    for alert in alerts:
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == alert.transaction_id
        ).first()

        results.append({
            "alert_id": alert.alert_id,
            "transaction_id": alert.transaction_id,
            "account_id": transaction.account_id if transaction else None,
            "amount": float(transaction.amount) if transaction else None,
            "transaction_type": transaction.transaction_type if transaction else None,
            "transaction_timestamp": (
                transaction.transaction_timestamp.isoformat()
                if transaction and transaction.transaction_timestamp
                else None
            ),
            "rule_id": alert.rule_id,
            "risk_score": alert.risk_score,
            "risk_level": alert.risk_level,
            "alert_status": alert.alert_status,
            "evidence": alert.evidence,
        })

    return {"total": len(results), "alerts": results}


# Cases

def serialize_case(case):
    return {
        "case_id": case.case_id,
        "case_title": case.case_title,
        "description": case.description,
        "priority": case.priority,
        "case_status": case.case_status,
        "assigned_analyst_id": case.assigned_analyst_id,
        "created_at": (
            case.created_at.isoformat() if case.created_at else None
        ),
        "due_at": case.due_at.isoformat() if case.due_at else None,
        "alert_count": len(case.alerts),
    }


@router.get("/cases")
def list_cases(
    case_status: str = None,
    priority: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(Case)

    if case_status:
        query = query.filter(
            Case.case_status == case_status.upper()
        )

    if priority:
        query = query.filter(
            Case.priority == priority.upper()
        )

    cases = query.order_by(Case.created_at.desc()).all()

    return {
        "total": len(cases),
        "cases": [serialize_case(case) for case in cases],
    }


@router.get("/cases/{case_id}")
def get_case_details(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(
        Case.case_id == case_id
    ).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    result = serialize_case(case)
    result["alerts"] = []

    for alert in case.alerts:
        result["alerts"].append({
            "alert_id": alert.alert_id,
            "transaction_id": alert.transaction_id,
            "rule_id": alert.rule_id,
            "risk_score": alert.risk_score,
            "risk_level": alert.risk_level,
            "alert_status": alert.alert_status,
            "evidence": alert.evidence,
        })

    return result


# Analyst workload

@router.get("/analysts")
def list_analysts(db: Session = Depends(get_db)):
    analysts = db.query(Analyst).order_by(
        Analyst.analyst_id
    ).all()

    results = []

    for analyst in analysts:
        workload = db.query(func.count(Case.case_id)).filter(
            Case.assigned_analyst_id == analyst.analyst_id,
            Case.case_status.in_(["OPEN", "IN_PROGRESS", "ESCALATED"]),
        ).scalar() or 0

        results.append({
            "analyst_id": analyst.analyst_id,
            "full_name": analyst.full_name,
            "role": analyst.role,
            "is_active": analyst.is_active,
            "active_case_count": workload,
        })

    return {"total": len(results), "analysts": results}


# Investigation actions

def run_action(function, *args):
    try:
        return function(*args)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/cases/{case_id}/start")
def start_investigation(
    case_id: str,
    request: AnalystRequest,
    db: Session = Depends(get_db),
):
    return run_action(
        start_case, db, case_id, request.analyst_id
    )


@router.post("/cases/{case_id}/comments")
def add_comment(
    case_id: str,
    request: CommentRequest,
    db: Session = Depends(get_db),
):
    return run_action(
        add_investigation_comment,
        db,
        case_id,
        request.analyst_id,
        request.comments,
    )


@router.post("/cases/{case_id}/escalate")
def escalate(
    case_id: str,
    request: CommentRequest,
    db: Session = Depends(get_db),
):
    return run_action(
        escalate_case,
        db,
        case_id,
        request.analyst_id,
        request.comments,
    )


@router.post("/cases/{case_id}/resolve")
def resolve(
    case_id: str,
    request: ResolveRequest,
    db: Session = Depends(get_db),
):
    return run_action(
        resolve_case,
        db,
        case_id,
        request.analyst_id,
        request.resolution,
        request.comments,
    )
