import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, utc_isoformat
from models import Group, User
from deps import get_current_user

router = APIRouter()


def _ensure_default_group(db: Session, user_id: int) -> Group:
    existing = db.query(Group).filter(Group.user_id == user_id, Group.group_key == "ungrouped").first()
    if not existing:
        existing = Group(user_id=user_id, group_key="ungrouped", name="未分组")
        db.add(existing)
        db.commit()
        db.refresh(existing)
    return existing


@router.get("/groups")
def get_groups(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ensure_default_group(db, user.id)
    rows = db.query(Group).filter(Group.user_id == user.id).all()
    return [{"id": r.group_key, "name": r.name, "createdAt": utc_isoformat(r.created_at)} for r in rows]


class GroupRequest(BaseModel):
    name: str


@router.post("/groups")
def create_group(req: GroupRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分组名称不能为空")
    existing = db.query(Group).filter(Group.user_id == user.id, Group.name == name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分组名称已存在，请使用其他名称")
    group_key = f"grp-{uuid.uuid4().hex[:12]}"
    g = Group(user_id=user.id, group_key=group_key, name=name)
    db.add(g)
    db.commit()
    db.refresh(g)
    return {"id": g.group_key, "name": g.name, "createdAt": utc_isoformat(g.created_at)}


@router.put("/groups/{group_key}")
def rename_group(group_key: str, req: GroupRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分组名称不能为空")
    g = db.query(Group).filter(Group.user_id == user.id, Group.group_key == group_key).first()
    if not g:
        raise HTTPException(status_code=404, detail="分组不存在")
    if g.group_key == "ungrouped":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能重命名默认分组")
    dup = db.query(Group).filter(Group.user_id == user.id, Group.name == name, Group.group_key != group_key).first()
    if dup:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分组名称已存在，请使用其他名称")
    g.name = name
    db.commit()
    return {"success": True}


@router.delete("/groups/{group_key}")
def delete_group(group_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = db.query(Group).filter(Group.user_id == user.id, Group.group_key == group_key).first()
    if not g:
        raise HTTPException(status_code=404, detail="分组不存在")
    if g.group_key == "ungrouped":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除默认分组")
    # 将仅属于该分组的文献移回"未分组"
    ungrouped = db.query(Group).filter(Group.user_id == user.id, Group.group_key == "ungrouped").first()
    for ref in list(g.references):
        other_groups = [grp for grp in ref.groups if grp.group_key != group_key]
        if not other_groups and ungrouped:
            ref.groups.append(ungrouped)
    db.delete(g)
    db.commit()
    return {"success": True}
