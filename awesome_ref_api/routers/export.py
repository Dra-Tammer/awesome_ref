import os
import time as _time
import uuid
from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Reference, Note, User, Group, DailyPlan, DailyTask
from deps import get_current_user
from routers.references import _to_dict, _make_ref_key, _apply_fields

router = APIRouter()

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _group_refs(groups: list[dict], references: list[dict]) -> list[dict]:
    """Organise references under their groups. Returns ordered group dicts."""
    group_map = {g["id"]: {**g, "refs": []} for g in groups}
    ungrouped_key = None
    for g in groups:
        if g.get("name") == "未分组" or g.get("id") == "ungrouped":
            ungrouped_key = g["id"]
    for ref in references:
        placed = False
        for gid in ref.get("groupIds", []):
            if gid in group_map:
                group_map[gid]["refs"].append(ref)
                placed = True
        if not placed and ungrouped_key and ungrouped_key in group_map:
            group_map[ungrouped_key]["refs"].append(ref)
    return list(group_map.values())


def _find_cjk_font() -> str | None:
    """Return path to an available CJK-capable TrueType font or None."""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


# ---------------------------------------------------------------------------
# Markdown generator
# ---------------------------------------------------------------------------

def _build_markdown(groups: list[dict], references: list[dict],
                    notes: dict, exported_at: str) -> str:
    grouped = _group_refs(groups, references)
    lines: list[str] = []
    lines.append("# AwesomeRef 导出数据")
    lines.append("")
    lines.append(f"**导出时间**: {exported_at}")
    lines.append(f"**文献数**: {len(references)}　**分组数**: {len(groups)}")
    lines.append("")

    for g in grouped:
        lines.append(f"## {g['name']}")
        lines.append("")
        if not g["refs"]:
            lines.append("*(空分组)*")
            lines.append("")
            continue
        for i, ref in enumerate(g["refs"], 1):
            authors = "; ".join(ref.get("authors") or [])
            title = ref.get("title") or "无标题"
            lines.append(f"### {i}. {title}")
            lines.append("")
            if authors:
                lines.append(f"- **作者**: {authors}")
            if ref.get("year"):
                lines.append(f"- **年份**: {ref['year']}")
            if ref.get("type"):
                lines.append(f"- **类型**: {ref['type']}")
            if ref.get("journal"):
                lines.append(f"- **期刊**: {ref['journal']}")
            if ref.get("volume"):
                lines.append(f"- **卷**: {ref['volume']}")
            if ref.get("issue"):
                lines.append(f"- **期**: {ref['issue']}")
            if ref.get("pages"):
                lines.append(f"- **页码**: {ref['pages']}")
            if ref.get("doi"):
                lines.append(f"- **DOI**: [{ref['doi']}](https://doi.org/{ref['doi']})")
            if ref.get("keywords"):
                lines.append(f"- **关键词**: {', '.join(ref['keywords'])}")
            lines.append("")
            if ref.get("abstract"):
                lines.append(f"**摘要**: {ref['abstract']}")
                lines.append("")
            ref_key = ref.get("id", "")
            if ref_key in notes and notes[ref_key].get("content"):
                lines.append(f"**笔记**: {notes[ref_key]['content']}")
                lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PDF generator (fpdf2)
# ---------------------------------------------------------------------------

def _build_pdf(groups: list[dict], references: list[dict],
               notes: dict, exported_at: str) -> BytesIO:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(12)
    pdf.set_right_margin(12)
    w = pdf.epw  # effective page width
    left_margin = pdf.l_margin

    cjk_path = _find_cjk_font()
    if cjk_path:
        pdf.add_font("cjk", "", cjk_path, uni=True)
        pdf.add_font("cjk", "B", cjk_path, uni=True)
        body_font = "cjk"
    else:
        body_font = "Helvetica"

    # ── header ──
    pdf.add_page()
    pdf.set_font(body_font, "B", 18)
    pdf.cell(w, 12, "AwesomeRef Export", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font(body_font, "", 9)
    pdf.cell(w, 6, f"Export time: {exported_at}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(w, 6, f"References: {len(references)}    Groups: {len(groups)}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    grouped = _group_refs(groups, references)

    for g in grouped:
        # ── group heading ──
        pdf.set_font(body_font, "B", 13)
        pdf.cell(w, 8, g["name"], new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y()
        pdf.set_draw_color(180)
        pdf.line(left_margin, y + 1, left_margin + w, y + 1)
        pdf.set_draw_color(0)
        pdf.ln(5)

        if not g["refs"]:
            pdf.set_font(body_font, "", 9)
            pdf.cell(w, 6, "(empty)", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            continue

        for i, ref in enumerate(g["refs"], 1):
            # Check if we need a page break before this reference
            # (keep at least 25mm of space for the first few lines)
            if pdf.y > pdf.h - 30:
                pdf.add_page()

            # ── reference title ──
            title = ref.get("title") or "Untitled"
            pdf.set_font(body_font, "B", 10.5)
            pdf.multi_cell(w, 5.5, f"{i}. {title}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(body_font, "", 9)

            # ── metadata block (label: value on same line) ──
            lines = []
            authors = "; ".join(ref.get("authors") or [])
            if authors:
                lines.append(("Authors:", authors))

            meta = []
            if ref.get("year"):
                meta.append(ref["year"])
            if ref.get("journal"):
                meta.append(ref["journal"])
            if ref.get("volume"):
                meta.append(f"Vol.{ref['volume']}")
            if ref.get("issue"):
                meta.append(f"No.{ref['issue']}")
            if ref.get("pages"):
                meta.append(f"pp.{ref['pages']}")
            if meta:
                lines.append(("Source:", "  ".join(meta)))

            if ref.get("doi"):
                lines.append(("DOI:", ref["doi"]))
            if ref.get("keywords"):
                lines.append(("Keywords:", ", ".join(ref["keywords"])))

            for label, value in lines:
                pdf.set_font(body_font, "B", 9)
                label_w = pdf.get_string_width(label + " ")
                pdf.cell(label_w, 5, label + " ")
                pdf.set_font(body_font, "", 9)
                pdf.multi_cell(w - label_w, 5, value, new_x="LMARGIN", new_y="NEXT")

            # ── abstract ──
            if ref.get("abstract"):
                pdf.ln(1.5)
                pdf.set_font(body_font, "B", 8.5)
                pdf.cell(w, 4.5, "Abstract:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font(body_font, "", 8.5)
                pdf.multi_cell(w, 4.5, ref["abstract"], new_x="LMARGIN", new_y="NEXT")

            # ── note ──
            ref_key = ref.get("id", "")
            if ref_key in notes and notes[ref_key].get("content"):
                pdf.ln(1.5)
                pdf.set_font(body_font, "B", 8.5)
                pdf.cell(w, 4.5, "Notes:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font(body_font, "", 8.5)
                pdf.multi_cell(w, 4.5, notes[ref_key]["content"],
                               new_x="LMARGIN", new_y="NEXT")

            # ── separator between references ──
            pdf.ln(2.5)
            y = pdf.get_y()
            pdf.set_draw_color(210)
            pdf.line(left_margin, y, left_margin + w, y)
            pdf.set_draw_color(0)
            pdf.ln(3)

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Word / docx generator (python-docx)
# ---------------------------------------------------------------------------

def _build_docx(groups: list[dict], references: list[dict],
                notes: dict, exported_at: str) -> BytesIO:
    from docx import Document
    from docx.shared import Pt, Inches

    doc = Document()
    style = doc.styles["Normal"]
    style.font.size = Pt(10.5)

    doc.add_heading("AwesomeRef Export", level=0)
    doc.add_paragraph(f"Export time: {exported_at}")
    doc.add_paragraph(f"References: {len(references)}    Groups: {len(groups)}")

    grouped = _group_refs(groups, references)
    for g in grouped:
        doc.add_heading(g["name"], level=1)
        if not g["refs"]:
            doc.add_paragraph("(empty)")
            continue
        for i, ref in enumerate(g["refs"], 1):
            doc.add_heading(f"{i}. {ref.get('title') or 'Untitled'}", level=2)
            authors = "; ".join(ref.get("authors") or [])
            if authors:
                doc.add_paragraph("Authors: ", style="List Bullet").add_run(authors)
            parts = []
            if ref.get("year"):
                parts.append(("Year", ref["year"]))
            if ref.get("type"):
                parts.append(("Type", ref["type"]))
            if ref.get("journal"):
                parts.append(("Journal", ref["journal"]))
            if ref.get("volume"):
                parts.append(("Volume", ref["volume"]))
            if ref.get("issue"):
                parts.append(("Issue", ref["issue"]))
            if ref.get("pages"):
                parts.append(("Pages", ref["pages"]))
            for label, val in parts:
                doc.add_paragraph(f"{label}: {val}", style="List Bullet")
            if ref.get("doi"):
                doc.add_paragraph(f"DOI: {ref['doi']}", style="List Bullet")
            if ref.get("keywords"):
                doc.add_paragraph("Keywords: ", style="List Bullet").add_run(
                    ", ".join(ref["keywords"]))
            if ref.get("abstract"):
                doc.add_paragraph("Abstract", style="List Bullet")
                doc.add_paragraph(ref["abstract"])
            ref_key = ref.get("id", "")
            if ref_key in notes and notes[ref_key].get("content"):
                p = doc.add_paragraph("Notes: ", style="List Bullet")
                p.add_run(notes[ref_key]["content"])
            doc.add_paragraph("─" * 40)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/export")
def export_data(
    fmt: str = Query("json", alias="format"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = [{"id": g.group_key, "name": g.name}
              for g in db.query(Group).filter(Group.user_id == user.id).all()]
    references = [
        _to_dict(r)
        for r in db.query(Reference)
                    .options(joinedload(Reference.groups))
                    .filter(Reference.user_id == user.id,
                            Reference.deleted_at.is_(None))
                    .all()
    ]
    notes = {n.ref_key: {"content": n.content}
             for n in db.query(Note).filter(Note.user_id == user.id).all()}

    daily_plans = []
    for plan in db.query(DailyPlan).filter(DailyPlan.user_id == user.id).all():
        tasks = sorted(plan.tasks, key=lambda t: (t.sort_order, t.id))
        daily_plans.append({
            "date": plan.date,
            "tasks": [{"title": t.title, "status": t.status, "note": t.note or "", "sortOrder": t.sort_order} for t in tasks],
        })

    exported_at = datetime.now(timezone.utc).isoformat()

    if fmt == "md":
        md_text = _build_markdown(groups, references, notes, exported_at)
        return Response(
            content=md_text.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition":
                     f"attachment; filename=awesomeref-export-{exported_at[:10]}.md"},
        )

    if fmt == "pdf":
        buf = _build_pdf(groups, references, notes, exported_at)
        return Response(
            content=buf.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition":
                     f"attachment; filename=awesomeref-export-{exported_at[:10]}.pdf"},
        )

    if fmt == "docx":
        buf = _build_docx(groups, references, notes, exported_at)
        return Response(
            content=buf.getvalue(),
            media_type="application/"
                        "vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition":
                     f"attachment; filename=awesomeref-export-{exported_at[:10]}.docx"},
        )

    # Default: json
    return {
        "export_version": "1.1",
        "exported_at": exported_at,
        "groups": groups,
        "references": references,
        "notes": notes,
        "daily_plans": daily_plans,
    }


class ImportData(BaseModel):
    export_version: str = ""
    exported_at: str = ""
    groups: list = []
    references: list = []
    notes: dict = {}
    daily_plans: list = []


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
            new_key = f"grp-{uuid.uuid4().hex[:12]}"
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

    import uuid as _uuid
    for item in data.references:
        title = (item.get("title") or "").strip()
        ref_key = _make_ref_key(title)
        # 处理 key 碰撞
        if ref_key in existing_refs and existing_refs[ref_key].title.lower().strip() != title.lower().strip():
            ref_key = ref_key + _uuid.uuid4().hex[:8]

        ref = existing_refs.get(ref_key)
        trashed_ref = trashed_refs.get(ref_key) if not ref else None

        if ref:
            _apply_fields(ref, item)
        elif trashed_ref:
            trashed_ref.deleted_at = None
            _apply_fields(trashed_ref, item)
            ref = trashed_ref
        else:
            ref = Reference(user_id=user.id, ref_key=ref_key)
            _apply_fields(ref, item)
            db.add(ref)
            db.flush()

        # Assign to groups
        raw_group_ids = item.get("groupIds", [])
        mapped_ids = [group_key_map.get(gid, gid) for gid in raw_group_ids]

        # 仅在导入数据包含分组信息时才清空现有分组
        if raw_group_ids:
            ref.groups.clear()
        if mapped_ids:
            for gid in mapped_ids:
                g = db.query(Group).filter(Group.user_id == user.id, Group.group_key == gid).first()
                if g:
                    ref.groups.append(g)
        if not ref.groups:
            ref.groups.append(ungrouped)

    db.commit()

    # Import notes (合并而非覆盖)
    for ref_key, note_data in data.notes.items():
        content = note_data.get("content", "").strip()
        if not content:
            continue
        now = datetime.now(timezone.utc)
        note = db.query(Note).filter(Note.user_id == user.id, Note.ref_key == ref_key).first()
        if note:
            existing = (note.content or "").strip()
            if existing and content and existing != content:
                note.content = existing + "\n\n---\n\n" + content
            elif not existing:
                note.content = content
            note.updated_at = now
        else:
            note = Note(user_id=user.id, ref_key=ref_key, content=content, updated_at=now)
            db.add(note)

    db.commit()

    # Import daily plans
    for plan_data in data.daily_plans:
        date = plan_data.get("date", "").strip()
        if not date:
            continue
        plan = db.query(DailyPlan).filter(DailyPlan.user_id == user.id, DailyPlan.date == date).first()
        if not plan:
            plan = DailyPlan(user_id=user.id, date=date)
            db.add(plan)
            db.flush()

        tasks_data = plan_data.get("tasks", [])
        # 追加新任务而非替换（按标题去重）
        existing_titles = {t.title for t in plan.tasks}
        max_order = max((t.sort_order for t in plan.tasks), default=-1)

        for td in tasks_data:
            title = td.get("title", "")
            if title in existing_titles:
                continue
            max_order += 1
            task = DailyTask(
                plan_id=plan.id,
                title=title,
                status=td.get("status", "pending"),
                note=td.get("note", ""),
                sort_order=td.get("sortOrder", max_order),
            )
            db.add(task)

    db.commit()
    return {"success": True}
