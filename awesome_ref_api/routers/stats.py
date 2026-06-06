import json
import os
from collections import Counter
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db, utc_isoformat
from deps import get_current_user
from models import User, Reference, Note, StandaloneNote, Group, DailyPlan, DailyTask

router = APIRouter()

PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pdf_data")
NOTE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "note_mark_data")
IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images_data")


def _dir_size_mb(path):
    if not os.path.isdir(path):
        return 0.0
    total = 0
    for f in os.listdir(path):
        fp = os.path.join(path, f)
        if os.path.isfile(fp):
            total += os.path.getsize(fp)
    return round(total / (1024 * 1024), 1)


@router.get("")
def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    uid = current_user.id
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Overview counts
    total_refs = db.query(func.count(Reference.id)).filter(
        Reference.user_id == uid, Reference.deleted_at.is_(None)
    ).scalar() or 0

    total_notes = db.query(func.count(StandaloneNote.id)).filter(
        StandaloneNote.user_id == uid
    ).scalar() or 0

    total_groups = db.query(func.count(Group.id)).filter(
        Group.user_id == uid
    ).scalar() or 0

    total_ref_notes = db.query(func.count(Note.id)).filter(
        Note.user_id == uid
    ).scalar() or 0

    # Trash count
    trash_count = db.query(func.count(Reference.id)).filter(
        Reference.user_id == uid, Reference.deleted_at.isnot(None)
    ).scalar() or 0

    # PDF attachment rate
    refs_with_pdf = db.query(func.count(Reference.id)).filter(
        Reference.user_id == uid,
        Reference.deleted_at.is_(None),
        Reference.pdf_filename.isnot(None),
        Reference.pdf_filename != "",
    ).scalar() or 0

    pdf_rate = round(refs_with_pdf / total_refs * 100, 1) if total_refs > 0 else 0

    # Note coverage: how many references have at least one note
    refs_with_notes = db.query(func.count(func.distinct(Note.ref_key))).filter(
        Note.user_id == uid
    ).scalar() or 0
    note_coverage = round(refs_with_notes / total_refs * 100, 1) if total_refs > 0 else 0

    # References with abstract
    refs_with_abstract = db.query(func.count(Reference.id)).filter(
        Reference.user_id == uid, Reference.deleted_at.is_(None),
        Reference.abstract.isnot(None), Reference.abstract != ""
    ).scalar() or 0

    # References with DOI
    refs_with_doi = db.query(func.count(Reference.id)).filter(
        Reference.user_id == uid, Reference.deleted_at.is_(None),
        Reference.doi.isnot(None), Reference.doi != ""
    ).scalar() or 0

    # This week / this month additions
    refs_this_week = db.query(func.count(Reference.id)).filter(
        Reference.user_id == uid, Reference.deleted_at.is_(None),
        Reference.created_at >= week_ago
    ).scalar() or 0

    refs_this_month = db.query(func.count(Reference.id)).filter(
        Reference.user_id == uid, Reference.deleted_at.is_(None),
        Reference.created_at >= month_ago
    ).scalar() or 0

    notes_this_week = db.query(func.count(StandaloneNote.id)).filter(
        StandaloneNote.user_id == uid, StandaloneNote.created_at >= week_ago
    ).scalar() or 0

    # Average authors per reference
    total_author_count = 0
    refs_authors_all = (
        db.query(Reference.authors_json)
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None))
        .all()
    )
    for (authors_str,) in refs_authors_all:
        if not authors_str:
            continue
        try:
            authors = json.loads(authors_str)
            if isinstance(authors, list):
                total_author_count += len([a for a in authors if a.strip()])
        except (json.JSONDecodeError, TypeError):
            continue
    avg_authors = round(total_author_count / total_refs, 1) if total_refs > 0 else 0

    # Year span
    year_rows_all = (
        db.query(Reference.year)
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None), Reference.year != "")
        .all()
    )
    years = [int(y[0]) for y in year_rows_all if y[0].isdigit()]
    year_span = f"{min(years)}–{max(years)}" if years else ""
    unique_years = len(set(years))

    # Storage stats
    pdf_size = _dir_size_mb(PDF_DIR)
    note_files = len([f for f in os.listdir(NOTE_DIR) if os.path.isfile(os.path.join(NOTE_DIR, f))]) if os.path.isdir(NOTE_DIR) else 0
    img_count = len([f for f in os.listdir(IMG_DIR) if os.path.isfile(os.path.join(IMG_DIR, f))]) if os.path.isdir(IMG_DIR) else 0

    # Most annotated references (top 5)
    annotated_rows = (
        db.query(Note.ref_key, func.count(Note.id))
        .filter(Note.user_id == uid)
        .group_by(Note.ref_key)
        .order_by(func.count(Note.id).desc())
        .limit(5)
        .all()
    )
    most_annotated = []
    for ref_key, cnt in annotated_rows:
        ref = db.query(Reference.title).filter(Reference.ref_key == ref_key, Reference.user_id == uid).first()
        if ref:
            most_annotated.append({"title": ref[0] or "无标题", "count": cnt})

    # Monthly addition trend (last 12 months)
    monthly_trend = []
    for i in range(11, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        else:
            next_month = now + timedelta(days=1)
        count = db.query(func.count(Reference.id)).filter(
            Reference.user_id == uid, Reference.deleted_at.is_(None),
            Reference.created_at >= month_start, Reference.created_at < next_month
        ).scalar() or 0
        monthly_trend.append({"month": month_start.strftime("%Y-%m"), "count": count})

    # Type distribution
    type_rows = (
        db.query(Reference.ref_type, func.count(Reference.id))
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None))
        .group_by(Reference.ref_type)
        .all()
    )
    type_distribution = {row[0] or "other": row[1] for row in type_rows}

    # Year distribution
    year_dist_rows = (
        db.query(Reference.year, func.count(Reference.id))
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None), Reference.year != "")
        .group_by(Reference.year)
        .order_by(Reference.year)
        .all()
    )
    year_distribution = {row[0]: row[1] for row in year_dist_rows}

    # Top journals
    journal_rows = (
        db.query(Reference.journal, func.count(Reference.id))
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None), Reference.journal != "")
        .group_by(Reference.journal)
        .order_by(func.count(Reference.id).desc())
        .limit(10)
        .all()
    )
    top_journals = [{"name": row[0], "count": row[1]} for row in journal_rows]

    # Top authors (parse JSON field)
    author_counter = Counter()
    for (authors_str,) in refs_authors_all:
        if not authors_str:
            continue
        try:
            authors = json.loads(authors_str)
            if isinstance(authors, list):
                author_counter.update(a.strip() for a in authors if a.strip())
        except (json.JSONDecodeError, TypeError):
            continue
    top_authors = [{"name": name, "count": count} for name, count in author_counter.most_common(10)]

    # Top keywords (parse JSON field)
    refs_keywords = (
        db.query(Reference.keywords_json)
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None))
        .all()
    )
    keyword_counter = Counter()
    for (kw_str,) in refs_keywords:
        if not kw_str:
            continue
        try:
            keywords = json.loads(kw_str)
            if isinstance(keywords, list):
                keyword_counter.update(k.strip() for k in keywords if k.strip())
        except (json.JSONDecodeError, TypeError):
            continue
    top_keywords = [{"keyword": kw, "count": count} for kw, count in keyword_counter.most_common(20)]

    # Recent activity
    recent_refs = (
        db.query(Reference.title, Reference.created_at)
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None))
        .order_by(Reference.created_at.desc())
        .limit(10)
        .all()
    )
    recent_notes = (
        db.query(StandaloneNote.title, StandaloneNote.updated_at)
        .filter(StandaloneNote.user_id == uid)
        .order_by(StandaloneNote.updated_at.desc())
        .limit(10)
        .all()
    )

    recent_tasks = (
        db.query(DailyTask.title, DailyTask.updated_at, DailyPlan.date)
        .join(DailyPlan, DailyTask.plan_id == DailyPlan.id)
        .filter(DailyPlan.user_id == uid)
        .order_by(DailyTask.updated_at.desc())
        .limit(10)
        .all()
    )

    activity = []
    for title, dt in recent_refs:
        if dt:
            activity.append({"type": "ref", "title": title or "无标题", "date": utc_isoformat(dt)})
    for title, dt in recent_notes:
        if dt:
            activity.append({"type": "note", "title": title or "无标题笔记", "date": utc_isoformat(dt)})
    for title, dt, plan_date in recent_tasks:
        if dt:
            activity.append({"type": "task", "title": title or "无标题任务", "date": utc_isoformat(dt), "planDate": plan_date})
    activity.sort(key=lambda x: x["date"], reverse=True)
    activity = activity[:20]

    return {
        "username": current_user.username,
        "registration_date": utc_isoformat(current_user.created_at),
        "total_references": total_refs,
        "total_standalone_notes": total_notes,
        "total_ref_notes": total_ref_notes,
        "total_groups": total_groups,
        "trash_count": trash_count,
        "pdf_attachment_rate": pdf_rate,
        "note_coverage": note_coverage,
        "refs_with_abstract": refs_with_abstract,
        "refs_with_doi": refs_with_doi,
        "refs_this_week": refs_this_week,
        "refs_this_month": refs_this_month,
        "notes_this_week": notes_this_week,
        "avg_authors": avg_authors,
        "year_span": year_span,
        "unique_years": unique_years,
        "pdf_size_mb": pdf_size,
        "note_files": note_files,
        "img_count": img_count,
        "most_annotated": most_annotated,
        "monthly_trend": monthly_trend,
        "type_distribution": type_distribution,
        "year_distribution": year_distribution,
        "top_journals": top_journals,
        "top_authors": top_authors,
        "top_keywords": top_keywords,
        "recent_activity": activity,
    }
