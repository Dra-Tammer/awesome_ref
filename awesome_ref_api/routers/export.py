import json
import hashlib
import time as _time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Reference, Note, User, Group
from deps import get_current_user

router = APIRouter()


def _ref_to_export(r: Reference) -> dict:
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
    }


@router.get("/export")
def export_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    groups = db.query(Group).filter(Group.user_id == user.id).all()
    references = db.query(Reference).filter(Reference.user_id == user.id, Reference.deleted_at.is_(None)).all()
    notes = db.query(Note).filter(Note.user_id == user.id).all()

    return {
        "export_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "groups": [{"id": g.group_key, "name": g.name} for g in groups],
        "references": [_ref_to_export(r) for r in references],
        "notes": {n.ref_key: {"content": n.content} for n in notes},
    }


class ImportData(BaseModel):
    export_version: str = ""
    exported_at: str = ""
    groups: list = []
    references: list = []
    notes: dict = {}


@router.post("/import")
def import_data(data: ImportData, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Build group name->key mapping from existing groups
    existing_groups = {g.name: g for g in db.query(Group).filter(Group.user_id == user.id).all()}
    group_key_map = {}  # old_key -> new_key

    for g in data.groups:
        name = (g.get("name") or "").strip()
        old_key = g.get("id", "")
        if not name:
            continue
        if name in existing_groups:
            group_key_map[old_key] = existing_groups[name].group_key
        else:
            new_key = f"grp-{int(_time.time() * 1000)}"
            new_group = Group(user_id=user.id, group_key=new_key, name=name)
            db.add(new_group)
            db.flush()
            existing_groups[name] = new_group
            group_key_map[old_key] = new_key

    # Ensure ungrouped exists
    ungrouped = db.query(Group).filter(Group.user_id == user.id, Group.group_key == "ungrouped").first()
    if not ungrouped:
        ungrouped = Group(user_id=user.id, group_key="ungrouped", name="未分组")
        db.add(ungrouped)
        db.flush()

    # Import references
    existing_refs = {r.ref_key: r for r in db.query(Reference).filter(Reference.user_id == user.id, Reference.deleted_at.is_(None)).all()}
    trashed_refs = {r.ref_key: r for r in db.query(Reference).filter(Reference.user_id == user.id, Reference.deleted_at.isnot(None)).all()}

    for item in data.references:
        title = (item.get("title") or "").strip()
        t = title.lower() if title else "untitled"
        ref_key = hashlib.md5(t.encode()).hexdigest()[:16]

        ref = existing_refs.get(ref_key)
        trashed_ref = trashed_refs.get(ref_key) if not ref else None

        if ref:
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
            ref = trashed_ref
        else:
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
            db.add(ref)
            db.flush()

        # Assign to groups
        raw_group_ids = item.get("groupIds", [])
        mapped_ids = [group_key_map.get(gid, gid) for gid in raw_group_ids]

        # Clear existing groups and reassign
        ref.groups.clear()
        if mapped_ids:
            for gid in mapped_ids:
                g = db.query(Group).filter(Group.user_id == user.id, Group.group_key == gid).first()
                if g:
                    ref.groups.append(g)
        if not ref.groups:
            ref.groups.append(ungrouped)

    db.commit()

    # Import notes
    for ref_key, note_data in data.notes.items():
        content = note_data.get("content", "")
        if not content:
            continue
        now = datetime.now(timezone.utc)
        note = db.query(Note).filter(Note.user_id == user.id, Note.ref_key == ref_key).first()
        if note:
            note.content = content
            note.updated_at = now
        else:
            note = Note(user_id=user.id, ref_key=ref_key, content=content, updated_at=now)
            db.add(note)

    db.commit()
    return {"success": True}
