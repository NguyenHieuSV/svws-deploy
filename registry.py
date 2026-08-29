# -*- coding: utf-8 -*-
"""
SVWS Design Registry — module FastAPI
=====================================
Chuẩn thiết kế "3D Design" + Sổ đăng ký thiết kế, lưu PostgreSQL,
lịch sử chỉnh sửa, AI soạn đề bài (gọi Anthropic phía server).

Cách gắn vào app hiện có (main.py):

    from svws_registry import registry

    app.include_router(registry.router)

    @app.on_event("startup")
    def _init_registry():
        registry.init_db()

Biến môi trường:
    DATABASE_URL       — có sẵn trên Render (postgres://... tự đổi thành postgresql://)
    ANTHROPIC_API_KEY  — key API Claude (bắt buộc để dùng nút AI)
    ANTHROPIC_MODEL    — mặc định "claude-sonnet-5"

URL sau khi deploy:  https://<app>.onrender.com/registry
"""
import os
import json
import datetime
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import HTMLResponse
from sqlalchemy import Column, JSON, Text
from sqlmodel import SQLModel, Field, Session, create_engine, select

# ----------------------------------------------------------------------------
# DB
# ----------------------------------------------------------------------------
_DB_URL = os.getenv("DATABASE_URL", "sqlite:///./svws_registry.db")
if _DB_URL.startswith("postgres://"):  # Render cấp dạng cũ
    _DB_URL = _DB_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(_DB_URL, pool_pre_ping=True)

_HERE = Path(__file__).resolve().parent
_SEED = _HERE / "registry_seed.json"
_PAGE = _HERE / "static" / "registry.html"

MAX_REVISIONS = 300  # giữ tối đa bao nhiêu bản lịch sử


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="microseconds")


class RegistryDoc(SQLModel, table=True):
    """Tài liệu chính — luôn chỉ có 1 dòng id=1 (nguồn chuẩn duy nhất)."""
    __tablename__ = "svws_registry_doc"
    id: int = Field(default=1, primary_key=True)
    data: dict = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: str = Field(default_factory=_now)
    updated_by: str = ""


class RegistryRevision(SQLModel, table=True):
    """Mỗi lần lưu tạo 1 bản snapshot để tra lịch sử / khôi phục."""
    __tablename__ = "svws_registry_revision"
    id: Optional[int] = Field(default=None, primary_key=True)
    data: dict = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: str = Field(default_factory=_now)
    updated_by: str = ""
    note: str = Field(default="", sa_column=Column(Text))


def init_db() -> None:
    """Tạo bảng nếu chưa có; nạp seed Rev.E nếu DB trống. Gọi ở startup."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        doc = s.get(RegistryDoc, 1)
        if doc is None:
            seed = json.loads(_SEED.read_text(encoding="utf-8")) if _SEED.exists() else {
                "meta": {"code": "SVWS-3D-REQ-001", "rev": "Rev.E", "date": "", "by": ""},
                "sections": [], "designs": [],
            }
            doc = RegistryDoc(id=1, data=seed, updated_at=_now(), updated_by="seed Rev.E")
            s.add(doc)
            s.add(RegistryRevision(data=seed, updated_at=doc.updated_at,
                                   updated_by="seed Rev.E", note="Khởi tạo từ file Rev.E"))
            s.commit()


# ----------------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------------
router = APIRouter(prefix="/registry", tags=["SVWS Design Registry"])


@router.get("", response_class=HTMLResponse, include_in_schema=False)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def page() -> str:
    """Giao diện app (single-file HTML)."""
    if not _PAGE.exists():
        raise HTTPException(500, "Thiếu file static/registry.html trong module")
    return _PAGE.read_text(encoding="utf-8")


@router.get("/api")
def get_doc():
    """Lấy toàn bộ tài liệu (chuẩn + sổ thiết kế)."""
    with Session(engine) as s:
        doc = s.get(RegistryDoc, 1)
        if doc is None:
            raise HTTPException(404, "Chưa khởi tạo — gọi init_db() ở startup")
        return {"data": doc.data, "updated_at": doc.updated_at, "updated_by": doc.updated_by}


@router.put("/api")
def save_doc(payload: dict = Body(...)):
    """Lưu toàn bộ tài liệu.

    Body: {data: {...}, updated_by: "Tên", base_updated_at: "..."}
    base_updated_at dùng chống ghi đè: nếu người khác đã lưu sau thời điểm
    mình tải trang thì trả 409 kèm bản mới nhất.
    """
    data = payload.get("data")
    if not isinstance(data, dict) or "sections" not in data:
        raise HTTPException(422, 'Body thiếu "data.sections"')
    who = (payload.get("updated_by") or "").strip()[:120] or "không rõ"
    base = payload.get("base_updated_at") or ""

    with Session(engine) as s:
        doc = s.get(RegistryDoc, 1)
        if doc is None:
            raise HTTPException(404, "Chưa khởi tạo")
        if base and base != doc.updated_at:
            return {"conflict": True, "data": doc.data,
                    "updated_at": doc.updated_at, "updated_by": doc.updated_by}
        doc.data = data
        doc.updated_at = _now()
        doc.updated_by = who
        s.add(doc)
        s.add(RegistryRevision(data=data, updated_at=doc.updated_at,
                               updated_by=who, note=payload.get("note", "")[:300]))
        # cắt bớt lịch sử cũ
        ids = s.exec(select(RegistryRevision.id)
                     .order_by(RegistryRevision.id.desc())).all()
        for old_id in ids[MAX_REVISIONS:]:
            old = s.get(RegistryRevision, old_id)
            if old:
                s.delete(old)
        s.commit()
        return {"conflict": False, "updated_at": doc.updated_at, "updated_by": who}


@router.get("/api/history")
def history(limit: int = 40):
    """Danh sách các lần lưu gần nhất (không kèm nội dung)."""
    with Session(engine) as s:
        rows = s.exec(select(RegistryRevision)
                      .order_by(RegistryRevision.id.desc())
                      .limit(max(1, min(limit, 200)))).all()
        return [{"id": r.id, "updated_at": r.updated_at,
                 "updated_by": r.updated_by, "note": r.note,
                 "n_designs": len((r.data or {}).get("designs", [])),
                 "n_items": sum(len(sec.get("items", []))
                                for sec in (r.data or {}).get("sections", []))}
                for r in rows]


@router.get("/api/history/{rid}")
def history_item(rid: int):
    with Session(engine) as s:
        r = s.get(RegistryRevision, rid)
        if r is None:
            raise HTTPException(404, "Không có bản lịch sử này")
        return {"id": r.id, "data": r.data, "updated_at": r.updated_at,
                "updated_by": r.updated_by, "note": r.note}


@router.post("/api/restore/{rid}")
def restore(rid: int, payload: dict = Body(default={})):
    """Khôi phục về một bản lịch sử (tự tạo thêm 1 revision mới ghi nhận việc này)."""
    who = (payload.get("updated_by") or "").strip()[:120] or "không rõ"
    with Session(engine) as s:
        r = s.get(RegistryRevision, rid)
        if r is None:
            raise HTTPException(404, "Không có bản lịch sử này")
        doc = s.get(RegistryDoc, 1)
        doc.data = r.data
        doc.updated_at = _now()
        doc.updated_by = who
        s.add(doc)
        s.add(RegistryRevision(data=r.data, updated_at=doc.updated_at, updated_by=who,
                               note=f"Khôi phục từ bản #{rid}"))
        s.commit()
        return {"ok": True, "updated_at": doc.updated_at}


# ----------------------------------------------------------------------------
# AI — gọi Anthropic phía server (key không lộ ra trình duyệt)
# ----------------------------------------------------------------------------
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _sections_summary(data: dict) -> str:
    lines = []
    for si, sec in enumerate(data.get("sections", []), 1):
        items = " | ".join(it.get("t", "") for it in sec.get("items", []))
        lines.append(f"{si}. {sec.get('title', '')}: {items}")
    return "\n".join(lines)


def _design_text(d: dict) -> str:
    def block(v):
        return "\n".join("    " + x for x in (v or "—").split("\n"))
    return "\n".join([
        f"• Mã thiết kế: {d.get('code') or '—'}",
        f"• Tên thiết kế: {d.get('name') or '—'}",
        f"• Công nghệ: {d.get('tech') or '—'}",
        f"• Công suất: {d.get('capacity') or '—'}",
        f"• Dự án / Khách hàng: {d.get('project') or '—'}",
        "• Thông số chính:", block(d.get("params")),
        "• Yêu cầu riêng:", block(d.get("notes")),
    ])


@router.post("/api/ai")
def ai_analyze(payload: dict = Body(...)):
    """AI đọc phiếu thiết kế, chỉ ra thông tin thiếu và chuẩn hóa mô tả.

    Body: {design: {...}, extra_answers: "..."}
    Trả về: {questions: [...], refined_A: "...", notes: "..."}
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(503, "Server chưa cấu hình ANTHROPIC_API_KEY "
                                 "(Render → Environment → thêm biến này)")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

    design = payload.get("design") or {}
    extra = (payload.get("extra_answers") or "").strip()
    extra_block = ("\nTHÔNG TIN BỔ SUNG NGƯỜI DÙNG VỪA TRẢ LỜI:\n" + extra) if extra else ""

    with Session(engine) as s:
        doc = s.get(RegistryDoc, 1)
        summary = _sections_summary(doc.data if doc else {})

    user_msg = f"""Bạn là kỹ sư trưởng của SVWS (công ty EPC xử lý nước / nước thải / khí thải, TP.HCM). Dưới đây là PHIẾU MÔ TẢ một thiết kế và TÓM TẮT bộ chuẩn "3D Design" của công ty.

PHIẾU THIẾT KẾ:
{_design_text(design)}
{extra_block}

TÓM TẮT CHUẨN 3D DESIGN:
{summary}

NHIỆM VỤ: (1) liệt kê tối đa 6 câu hỏi về thông tin CÒN THIẾU quan trọng nhất để thiết kế được (nếu đủ thì để mảng rỗng); (2) viết "refined_A": mô tả thiết kế chuẩn hóa, gọn, đủ, kỹ thuật, tiếng Việt, dạng gạch đầu dòng, gộp cả thông tin bổ sung nếu có; (3) "notes": 1-2 lưu ý kỹ thuật đáng chú ý (nếu có).

CHỈ trả về JSON hợp lệ, không markdown, không giải thích:
{{"questions":["..."],"refined_A":"...","notes":"..."}}"""

    try:
        resp = httpx.post(
            _ANTHROPIC_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": user_msg}],
            },
            timeout=90.0,
        )
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Không gọi được Anthropic API: {e}")

    if resp.status_code != 200:
        raise HTTPException(502, f"Anthropic API lỗi {resp.status_code}: {resp.text[:300]}")

    out = resp.json()
    text = "\n".join(b.get("text", "") for b in out.get("content", [])
                     if b.get("type") == "text")
    clean = text.replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        # AI trả không đúng JSON — vẫn đưa nội dung về cho người dùng đọc
        parsed = {"questions": [], "refined_A": clean,
                  "notes": "AI trả lời không đúng định dạng JSON — nội dung thô ở trên."}
    return {
        "questions": parsed.get("questions") or [],
        "refined_A": parsed.get("refined_A") or "",
        "notes": parsed.get("notes") or "",
    }
