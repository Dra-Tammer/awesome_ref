import os
import re
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import StandaloneNote, User
from deps import get_current_user

router = APIRouter()

NOTES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "note_mark_data")
IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images_data")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


def _ensure_notes_dir():
    os.makedirs(NOTES_DIR, exist_ok=True)


def _ensure_images_dir():
    os.makedirs(IMAGES_DIR, exist_ok=True)


def _safe_filename(title: str, note_id: int) -> str:
    """生成安全的文件名: 标题_序号.md"""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title).strip()
    # 防止路径穿越: 移除连续的点
    name = re.sub(r'\.{2,}', '', name)
    if not name:
        name = "无标题笔记"
    return f"{name}_{note_id}.md"


def _read_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def _write_file(filepath: str, content: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


@router.get("/standalone-notes")
def list_notes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(StandaloneNote).filter(StandaloneNote.user_id == user.id).order_by(StandaloneNote.updated_at.desc()).all()
    result = []
    for n in rows:
        if not n.filename:
            continue
        filepath = os.path.join(NOTES_DIR, n.filename)
        content = _read_file(filepath)
        result.append({
            "id": n.id,
            "title": n.title,
            "content": content,
            "createdAt": n.created_at.isoformat() if n.created_at else "",
            "updatedAt": n.updated_at.isoformat() if n.updated_at else "",
        })
    return result


class NoteCreateRequest(BaseModel):
    title: str = "无标题笔记"


@router.post("/standalone-notes")
def create_note(req: NoteCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    # 先创建 DB 记录拿到 id，再用 id 生成文件名
    note = StandaloneNote(user_id=user.id, title=req.title, filename="", created_at=now, updated_at=now)
    db.add(note)
    db.flush()
    # 用 id 生成文件名
    filename = _safe_filename(req.title, note.id)
    note.filename = filename
    db.commit()
    db.refresh(note)
    # 创建空 .md 文件
    _ensure_notes_dir()
    filepath = os.path.join(NOTES_DIR, filename)
    _write_file(filepath, "")
    return {
        "id": note.id,
        "title": note.title,
        "content": "",
        "createdAt": note.created_at.isoformat(),
        "updatedAt": note.updated_at.isoformat(),
    }


class NoteUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None


@router.put("/standalone-notes/{note_id}")
def update_note(note_id: int, req: NoteUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(StandaloneNote).filter(StandaloneNote.id == note_id, StandaloneNote.user_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    _ensure_notes_dir()

    # 如果 filename 为空（异常情况），先用当前标题补一个
    if not note.filename:
        note.filename = _safe_filename(note.title, note.id)

    current_path = os.path.join(NOTES_DIR, note.filename)

    # 更新标题 → 重命名文件
    if req.title is not None:
        note.title = req.title
        new_filename = _safe_filename(req.title, note.id)
        new_path = os.path.join(NOTES_DIR, new_filename)
        if os.path.exists(current_path) and current_path != new_path:
            os.rename(current_path, new_path)
        note.filename = new_filename
        current_path = new_path

    # 更新内容 → 写入文件
    if req.content is not None:
        _write_file(current_path, req.content)

    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    content = _read_file(os.path.join(NOTES_DIR, note.filename))
    return {
        "id": note.id,
        "title": note.title,
        "content": content,
        "createdAt": note.created_at.isoformat(),
        "updatedAt": note.updated_at.isoformat(),
    }


@router.delete("/standalone-notes/{note_id}")
def delete_note(note_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(StandaloneNote).filter(StandaloneNote.id == note_id, StandaloneNote.user_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    # 删除 .md 文件
    if note.filename:
        filepath = os.path.join(NOTES_DIR, note.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    db.delete(note)
    db.commit()
    return {"success": True}


@router.post("/standalone-notes/images")
async def upload_image(file: UploadFile, user: User = Depends(get_current_user)):
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
    return {"success": True, "url": f"/api/standalone-notes/images/{filename}"}


@router.get("/standalone-notes/images/{filename}")
def get_image(filename: str, user: User = Depends(get_current_user)):
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
