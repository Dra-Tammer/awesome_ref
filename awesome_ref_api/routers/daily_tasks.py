from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

from database import get_db, utc_isoformat
from models import User, DailyPlan, DailyTask
from deps import get_current_user

router = APIRouter()


class TaskCreateRequest(BaseModel):
    plan_id: int
    title: str


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    status: str | None = None
    note: str | None = None
    sort_order: int | None = None


def _task_to_dict(task: DailyTask) -> dict:
    return {
        "id": task.id,
        "planId": task.plan_id,
        "title": task.title,
        "status": task.status,
        "note": task.note or "",
        "sortOrder": task.sort_order,
        "createdAt": utc_isoformat(task.created_at),
        "updatedAt": utc_isoformat(task.updated_at),
    }


def _plan_to_dict(plan: DailyPlan) -> dict:
    tasks = sorted(plan.tasks, key=lambda t: (t.sort_order, t.id), reverse=True)
    return {
        "id": plan.id,
        "date": plan.date,
        "createdAt": utc_isoformat(plan.created_at),
        "tasks": [_task_to_dict(t) for t in tasks],
    }


@router.get("/daily-tasks/today")
def get_today_plan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    plan = db.query(DailyPlan).filter(
        DailyPlan.user_id == user.id,
        DailyPlan.date == today,
    ).first()

    if not plan:
        plan = DailyPlan(user_id=user.id, date=today)
        db.add(plan)
        db.commit()
        db.refresh(plan)

    return _plan_to_dict(plan)


@router.get("/daily-tasks/plan/{date}")
def get_plan_by_date(
    date: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.query(DailyPlan).filter(
        DailyPlan.user_id == user.id,
        DailyPlan.date == date,
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="该日期没有计划")

    return _plan_to_dict(plan)


@router.post("/daily-tasks/plan/{date}")
def create_plan_for_date(
    date: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(DailyPlan).filter(
        DailyPlan.user_id == user.id,
        DailyPlan.date == date,
    ).first()

    if existing:
        return _plan_to_dict(existing)

    plan = DailyPlan(user_id=user.id, date=date)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(plan)


@router.get("/daily-tasks/search")
def search_tasks(
    q: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    keyword = q.strip()
    if not keyword:
        return []

    words = keyword.lower().split()
    query = db.query(DailyTask).join(DailyPlan).filter(
        DailyPlan.user_id == user.id,
    )
    for w in words:
        query = query.filter(
            DailyTask.title.ilike(f"%{w}%") | DailyTask.note.ilike(f"%{w}%")
        )

    results = []
    for task in query.limit(20).all():
        results.append({
            **_task_to_dict(task),
            "date": task.plan.date,
        })

    return results


@router.get("/daily-tasks/heatmap")
def get_heatmap(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    since = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")
    plans = db.query(DailyPlan).filter(
        DailyPlan.user_id == user.id,
        DailyPlan.date >= since,
    ).all()

    result = []
    for plan in plans:
        total = len(plan.tasks)
        done = sum(1 for t in plan.tasks if t.status == "done")
        partial = sum(1 for t in plan.tasks if t.status == "partial")
        result.append({
            "date": plan.date,
            "total": total,
            "done": done,
            "partial": partial,
        })

    return result


@router.post("/daily-tasks")
def create_task(
    req: TaskCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.query(DailyPlan).filter(
        DailyPlan.id == req.plan_id,
        DailyPlan.user_id == user.id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")

    max_order = db.query(func.max(DailyTask.sort_order)).filter(
        DailyTask.plan_id == plan.id,
    ).scalar() or 0

    task = DailyTask(
        plan_id=plan.id,
        title=req.title,
        sort_order=max_order + 1,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_to_dict(task)


@router.put("/daily-tasks/{task_id}")
def update_task(
    task_id: int,
    req: TaskUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(DailyTask).join(DailyPlan).filter(
        DailyTask.id == task_id,
        DailyPlan.user_id == user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if req.title is not None:
        task.title = req.title
    if req.status is not None:
        if req.status not in ("pending", "partial", "done"):
            raise HTTPException(status_code=400, detail="状态值无效")
        task.status = req.status
    if req.note is not None:
        task.note = req.note
    if req.sort_order is not None:
        task.sort_order = req.sort_order

    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return _task_to_dict(task)


@router.delete("/daily-tasks/{task_id}")
def delete_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(DailyTask).join(DailyPlan).filter(
        DailyTask.id == task_id,
        DailyPlan.user_id == user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(task)
    db.commit()
    return {"success": True}
