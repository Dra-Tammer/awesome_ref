import json
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
from models import User, Reference, Note, StandaloneNote, Group

router = APIRouter()


@router.get("")
def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    uid = current_user.id

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

    # PDF attachment rate
    refs_with_pdf = db.query(func.count(Reference.id)).filter(
        Reference.user_id == uid,
        Reference.deleted_at.is_(None),
        Reference.pdf_filename.isnot(None),
        Reference.pdf_filename != "",
    ).scalar() or 0

    pdf_rate = round(refs_with_pdf / total_refs * 100, 1) if total_refs > 0 else 0

    # Type distribution
    type_rows = (
        db.query(Reference.ref_type, func.count(Reference.id))
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None))
        .group_by(Reference.ref_type)
        .all()
    )
    type_distribution = {row[0] or "other": row[1] for row in type_rows}

    # Year distribution
    year_rows = (
        db.query(Reference.year, func.count(Reference.id))
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None), Reference.year != "")
        .group_by(Reference.year)
        .order_by(Reference.year)
        .all()
    )
    year_distribution = {row[0]: row[1] for row in year_rows}

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
    refs_authors = (
        db.query(Reference.authors_json)
        .filter(Reference.user_id == uid, Reference.deleted_at.is_(None))
        .all()
    )
    author_counter = Counter()
    for (authors_str,) in refs_authors:
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

    activity = []
    for title, dt in recent_refs:
        if dt:
            activity.append({"type": "ref", "title": title or "无标题", "date": dt.isoformat()})
    for title, dt in recent_notes:
        if dt:
            activity.append({"type": "note", "title": title or "无标题笔记", "date": dt.isoformat()})
    activity.sort(key=lambda x: x["date"], reverse=True)
    activity = activity[:20]

    return {
        "username": current_user.username,
        "registration_date": current_user.created_at.isoformat() if current_user.created_at else "",
        "total_references": total_refs,
        "total_standalone_notes": total_notes,
        "total_ref_notes": total_ref_notes,
        "total_groups": total_groups,
        "pdf_attachment_rate": pdf_rate,
        "type_distribution": type_distribution,
        "year_distribution": year_distribution,
        "top_journals": top_journals,
        "top_authors": top_authors,
        "top_keywords": top_keywords,
        "recent_activity": activity,
    }
