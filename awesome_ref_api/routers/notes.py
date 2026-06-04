import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, utc_isoformat
from models import Note, User
from deps import get_current_user

router = APIRouter()

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images_data")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


def _ensure_images_dir():
    os.makedirs(IMAGES_DIR, exist_ok=True)


@router.get("/notes")
def get_notes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Note).filter(Note.user_id == user.id).all()
    result = {}
    for n in rows:
        result[n.ref_key] = {"content": n.content, "updatedAt": utc_isoformat(n.updated_at)}
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
    return {"success": True, "note": {"content": note.content, "updatedAt": utc_isoformat(note.updated_at)}}


@router.delete("/notes/{ref_key}")
def delete_note(ref_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.user_id == user.id, Note.ref_key == ref_key).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    db.delete(note)
    db.commit()
    return {"success": True}


@router.post("/notes/images")
async def upload_note_image(file: UploadFile, user: User = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/GIF/WebP/BMP 格式")
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 10MB")
    _ensure_images_dir()
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(IMAGES_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)
    return {"success": True, "url": f"/api/notes/images/{filename}"}


@router.get("/notes/images/{filename}")
def get_note_image(filename: str, user: User = Depends(get_current_user)):
    path = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="图片不存在")
    ext = os.path.splitext(filename)[1].lower()
    media_types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp", ".bmp": "image/bmp",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    return FileResponse(path, media_type=media_type, content_disposition_type="inline")
