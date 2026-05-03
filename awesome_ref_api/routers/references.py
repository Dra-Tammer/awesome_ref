import json
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Reference, Note, User, Group
from deps import get_current_user

router = APIRouter()


def _make_ref_key(title: str) -> str:
    """根据标题生成唯一的文献ID"""
    t = (title or "").strip().lower()
    if not t:
        t = "untitled"
    return hashlib.md5(t.encode()).hexdigest()[:16]


class ReferenceItem(BaseModel):
    title: str = ""
    type: str = ""
    authors: list = []
    year: str = ""
    journal: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    abstract: str = ""
    doi: str = ""
    keywords: list = []


@router.get("/references")
def get_references(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Reference).filter(Reference.user_id == user.id, Reference.deleted_at.is_(None)).all()
    return [_to_dict(r) for r in rows]


def _purge_old_trash(db: Session, user_id: int):
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    old_refs = db.query(Reference).filter(
        Reference.user_id == user_id,
        Reference.deleted_at.isnot(None),
        Reference.deleted_at < cutoff,
    ).all()
    for ref in old_refs:
        db.query(Note).filter(Note.user_id == user_id, Note.ref_key == ref.ref_key).delete()
        db.delete(ref)
    if old_refs:
        db.commit()


@router.get("/references/trash")
def get_trash(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _purge_old_trash(db, user.id)
    rows = db.query(Reference).filter(
        Reference.user_id == user.id, Reference.deleted_at.isnot(None)
    ).all()
    return [_to_dict(r) for r in rows]


@router.delete("/references/trash")
def clear_trash(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trashed = db.query(Reference).filter(
        Reference.user_id == user.id, Reference.deleted_at.isnot(None)
    ).all()
    for ref in trashed:
        db.query(Note).filter(Note.user_id == user.id, Note.ref_key == ref.ref_key).delete()
        db.delete(ref)
    db.commit()
    return {"success": True, "count": len(trashed)}


@router.post("/references")
def save_references(items: list[ReferenceItem], user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = [item.model_dump() for item in items]

    # 确保"未分组"存在
    ungrouped = db.query(Group).filter(Group.user_id == user.id, Group.group_key == "ungrouped").first()
    if not ungrouped:
        ungrouped = Group(user_id=user.id, group_key="ungrouped", name="未分组")
        db.add(ungrouped)
        db.flush()

    existing = {r.ref_key: r for r in db.query(Reference).filter(Reference.user_id == user.id, Reference.deleted_at.is_(None)).all()}
    trashed = {r.ref_key: r for r in db.query(Reference).filter(Reference.user_id == user.id, Reference.deleted_at.isnot(None)).all()}
    imported_keys = set()

    for item in data:
        title = (item.get("title") or "").strip()
        ref_key = _make_ref_key(title)
        imported_keys.add(ref_key)
        ref = existing.get(ref_key)
        trashed_ref = trashed.get(ref_key) if not ref else None

        if ref:
            # 更新文献信息，保留原有分组关系和笔记
            ref.ref_type = item.get("type", "")
            ref.title = title
            ref.authors_json = json.dumps(item.get("authors", []), ensure_ascii=False)
            ref.year = item.get("year", "")
            ref.journal = item.get("journal", "")
            ref.volume = item.get("volume", "")
            ref.issue = item.get("issue", "")
            ref.pages = item.get("pages", "")
            ref.abstract = item.get("abstract", "")
            ref.doi = item.get("doi", "")
            ref.keywords_json = json.dumps(item.get("keywords", []), ensure_ascii=False)
        elif trashed_ref:
            # 从回收站恢复并更新
            trashed_ref.deleted_at = None
            trashed_ref.ref_type = item.get("type", "")
            trashed_ref.title = title
            trashed_ref.authors_json = json.dumps(item.get("authors", []), ensure_ascii=False)
            trashed_ref.year = item.get("year", "")
            trashed_ref.journal = item.get("journal", "")
            trashed_ref.volume = item.get("volume", "")
            trashed_ref.issue = item.get("issue", "")
            trashed_ref.pages = item.get("pages", "")
            trashed_ref.abstract = item.get("abstract", "")
            trashed_ref.doi = item.get("doi", "")
            trashed_ref.keywords_json = json.dumps(item.get("keywords", []), ensure_ascii=False)
        else:
            # 新文献，加入"未分组"
            ref = Reference(
                user_id=user.id,
                ref_key=ref_key,
                ref_type=item.get("type", ""),
                title=title,
                authors_json=json.dumps(item.get("authors", []), ensure_ascii=False),
                year=item.get("year", ""),
                journal=item.get("journal", ""),
                volume=item.get("volume", ""),
                issue=item.get("issue", ""),
                pages=item.get("pages", ""),
                abstract=item.get("abstract", ""),
                doi=item.get("doi", ""),
                keywords_json=json.dumps(item.get("keywords", []), ensure_ascii=False),
            )
            ref.groups.append(ungrouped)
            db.add(ref)

    db.commit()
    return {"success": True, "count": len(imported_keys)}


@router.post("/references/{ref_key}/groups/{group_key}")
def add_ref_to_group(ref_key: str, group_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(Reference).filter(Reference.user_id == user.id, Reference.ref_key == ref_key).first()
    if not ref:
        raise HTTPException(status_code=404, detail="文献不存在")
    group = db.query(Group).filter(Group.user_id == user.id, Group.group_key == group_key).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    if group not in ref.groups:
        ref.groups.append(group)
        # 加入非"未分组"分组时，自动从"未分组"移除
        if group_key != "ungrouped":
            ungrouped = next((g for g in ref.groups if g.group_key == "ungrouped"), None)
            if ungrouped:
                ref.groups.remove(ungrouped)
        db.commit()
    return {"success": True}


@router.delete("/references/{ref_key}/groups/{group_key}")
def remove_ref_from_group(ref_key: str, group_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(Reference).filter(Reference.user_id == user.id, Reference.ref_key == ref_key).first()
    if not ref:
        raise HTTPException(status_code=404, detail="文献不存在")
    group = db.query(Group).filter(Group.user_id == user.id, Group.group_key == group_key).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    if group in ref.groups:
        ref.groups.remove(group)
        # 从所有分组移除后，自动回到"未分组"
        if len(ref.groups) == 0:
            ungrouped = db.query(Group).filter(Group.user_id == user.id, Group.group_key == "ungrouped").first()
            if ungrouped:
                ref.groups.append(ungrouped)
        db.commit()
    return {"success": True}


@router.delete("/references/{ref_key}")
def soft_delete_reference(ref_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(Reference).filter(Reference.user_id == user.id, Reference.ref_key == ref_key).first()
    if not ref:
        raise HTTPException(status_code=404, detail="文献不存在")
    ref.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True}


@router.post("/references/{ref_key}/restore")
def restore_reference(ref_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(Reference).filter(Reference.user_id == user.id, Reference.ref_key == ref_key).first()
    if not ref:
        raise HTTPException(status_code=404, detail="文献不存在")
    if ref.deleted_at is None:
        raise HTTPException(status_code=400, detail="文献不在回收站中")
    ref.deleted_at = None
    db.commit()
    return {"success": True}


@router.delete("/references/{ref_key}/permanent")
def permanent_delete_reference(ref_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(Reference).filter(Reference.user_id == user.id, Reference.ref_key == ref_key).first()
    if not ref:
        raise HTTPException(status_code=404, detail="文献不存在")
    if ref.deleted_at is None:
        raise HTTPException(status_code=400, detail="请先将文献移入回收站")
    db.query(Note).filter(Note.user_id == user.id, Note.ref_key == ref_key).delete()
    db.delete(ref)
    db.commit()
    return {"success": True}


def _to_dict(r: Reference) -> dict:
    return {
        "id": r.ref_key,
        "type": r.ref_type,
        "title": r.title,
        "authors": json.loads(r.authors_json) if r.authors_json else [],
        "year": r.year,
        "journal": r.journal,
        "volume": r.volume,
        "issue": r.issue,
        "pages": r.pages,
        "abstract": r.abstract,
        "doi": r.doi,
        "keywords": json.loads(r.keywords_json) if r.keywords_json else [],
        "groupIds": [g.group_key for g in r.groups],
        "deletedAt": r.deleted_at.isoformat() if r.deleted_at else None,
    }
