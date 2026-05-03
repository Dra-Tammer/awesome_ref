from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Note, User
from deps import get_current_user

router = APIRouter()


@router.get("/notes")
def get_notes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Note).filter(Note.user_id == user.id).all()
    result = {}
    for n in rows:
        result[n.ref_key] = {"content": n.content, "updatedAt": n.updated_at.isoformat() if n.updated_at else ""}
    return result


class NoteRequest(BaseModel):
    refId: str
    content: str


@router.post("/notes")
def save_note(req: NoteRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref_key = req.refId.strip()
    if not ref_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refId不能为空")
    now = datetime.now(timezone.utc)
    note = db.query(Note).filter(Note.user_id == user.id, Note.ref_key == ref_key).first()
    if note:
        note.content = req.content
        note.updated_at = now
    else:
        note = Note(user_id=user.id, ref_key=ref_key, content=req.content, updated_at=now)
        db.add(note)
    db.commit()
    db.refresh(note)
    return {"success": True, "note": {"content": note.content, "updatedAt": note.updated_at.isoformat()}}


@router.delete("/notes/{ref_key}")
def delete_note(ref_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.user_id == user.id, Note.ref_key == ref_key).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    db.delete(note)
    db.commit()
    return {"success": True}
