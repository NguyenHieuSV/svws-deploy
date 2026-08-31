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
import re
import json
import datetime
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Body, Response, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
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
_THREE = _HERE / "static" / "three.min.js"   # Three.js r128 (MIT) — chuẩn Rev.E
_SVWS3D = _HERE / "static" / "svws3d.js"     # bộ dựng hình chuẩn của SVWS

MAX_REVISIONS = 300  # giữ tối đa bao nhiêu bản lịch sử

# Địa chỉ công khai của app — tool tải về gọi ngược lại đây để dùng AI mà không
# phải ôm API key. Đổi được qua env nếu sau này dời tên miền.
_PUBLIC_URL = os.getenv("SVWS_PUBLIC_URL", "https://svws-app-iit7.onrender.com").rstrip("/")


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


@router.get("/three.js", include_in_schema=False)
def three_js():
    """Three.js r128 để nhúng vào tool sinh ra.

    AI không thể gõ tay 600KB thư viện (vượt xa trần token) nên trước đây nó tự
    hạ cấp xuống canvas 2D. Nay AI chỉ viết phần cảnh, chỗ thư viện để trống
    bằng dấu hiệu, client nạp file này chèn vào → tool vẫn single-file offline.
    """
    if not _THREE.exists():
        raise HTTPException(500, "Thiếu static/three.min.js trong module")
    return Response(_THREE.read_text(encoding="utf-8"),
                    media_type="application/javascript; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=31536000, immutable"})


@router.get("/svws3d.js", include_in_schema=False)
def svws3d_js():
    """Bộ dựng hình chuẩn: bố cục theo hàng, ống vuông góc, camera tự căn khung.

    AI gõ toạ độ mà không nhìn thấy kết quả nên bố cục hay hỏng. Thư viện này
    nhận phần đó; AI chỉ khai báo danh sách thiết bị và đường nối.
    """
    if not _SVWS3D.exists():
        raise HTTPException(500, "Thiếu static/svws3d.js trong module")
    return Response(_SVWS3D.read_text(encoding="utf-8"),
                    media_type="application/javascript; charset=utf-8",
                    headers={"Cache-Control": "no-cache"})


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


def _loi_ai_vn(status: int, body: str) -> str:
    """Dịch lỗi của Anthropic sang tiếng Việt kèm CHỖ SỬA.

    Nguyên văn tiếng Anh dán lên màn hình thì người dùng không biết phải làm gì
    — mấy lỗi hay gặp đều là chuyện tài khoản, sửa ở Console chứ không phải lỗi app.
    """
    b = (body or "")
    low = b.lower()
    khi_nao = ""
    m = re.search(r"regain access on ([0-9]{4}-[0-9]{2}-[0-9]{2}) at ([0-9]{2}:[0-9]{2})", b)
    if m:
        try:  # giờ UTC → giờ Việt Nam cho dễ hình dung
            t = datetime.datetime.fromisoformat(m.group(1) + "T" + m.group(2) + ":00+00:00")
            vn = t.astimezone(datetime.timezone(datetime.timedelta(hours=7)))
            khi_nao = f" Hạn mức tự mở lại lúc {vn:%H:%M ngày %d/%m/%Y} (giờ Việt Nam)."
        except ValueError:
            khi_nao = f" Mở lại lúc {m.group(2)} UTC ngày {m.group(1)}."

    if "usage limit" in low or "spend limit" in low:
        return ("Tài khoản Anthropic đã CHẠM HẠN MỨC CHI TIÊU do chính mình đặt "
                "(không phải hết tiền, cũng không phải lỗi app)." + khi_nao +
                " Muốn dùng ngay thì vào console.anthropic.com → Settings → Limits "
                "để nâng hạn mức. Trong lúc chờ, nút '📄 Đề bài nhanh (không AI)' và "
                "'📋 Copy đề bài' vẫn dùng bình thường.")
    if "credit balance" in low:
        return ("Tài khoản Anthropic đã HẾT CREDIT. Vào console.anthropic.com → "
                "Plans & Billing để nạp thêm. Trong lúc chờ, nút '📄 Đề bài nhanh "
                "(không AI)' vẫn dùng được.")
    if status == 429 or "rate_limit" in low:
        return "Gọi AI quá nhanh (quá giới hạn số lượt/phút). Chờ khoảng một phút rồi thử lại."
    if status == 401 or "authentication" in low or "invalid x-api-key" in low:
        return ("Khóa ANTHROPIC_API_KEY sai hoặc đã bị thu hồi. Kiểm tra lại trong "
                "Render → Environment.")
    if "model" in low and ("not found" in low or "does not exist" in low):
        return ("Mã model trong ANTHROPIC_MODEL không còn phục vụ — đổi sang model "
                "hiện hành trong Render → Environment.")
    return f"Anthropic API lỗi {status}: {b[:300]}"


def _goi_ai_json(api_key: str, model: str, content, max_tokens: int,
                 system: str = "", timeout: float = 300.0, tra_tho: bool = False):
    """Gọi Claude và ép câu trả lời về JSON.

    BẪY: token SUY NGHĨ (adaptive thinking) TÍNH VÀO max_tokens. Để trần thấp thì
    model nghĩ hết hạn mức rồi JSON bị cắt giữa chừng, parse hỏng — và thông báo
    lỗi lại đổ oan cho "file khó đọc". Vì vậy: trần rộng, hãm mức suy nghĩ, và
    khi chạm trần thì nói đúng bệnh.

    tra_tho=True: parse hỏng thì trả {"__tho__": <văn bản>} thay vì ném lỗi.
    """
    body = {"model": model, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": content}]}
    if system:
        body["system"] = system
    effort = os.getenv("ANTHROPIC_EFFORT", "medium")
    if effort:
        body["output_config"] = {"effort": effort}
    try:
        resp = httpx.post(_ANTHROPIC_URL,
                          headers={"x-api-key": api_key,
                                   "anthropic-version": "2023-06-01",
                                   "content-type": "application/json"},
                          json=body, timeout=timeout)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Không gọi được Anthropic API: {e}")
    if resp.status_code != 200:
        raise HTTPException(502, _loi_ai_vn(resp.status_code, resp.text))

    out = resp.json()
    text = "\n".join(b.get("text", "") for b in out.get("content", [])
                     if b.get("type") == "text")
    stop = out.get("stop_reason")
    used = (out.get("usage") or {}).get("output_tokens", "?")
    clean = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    m = re.search(r"[\{\[][\s\S]*[\}\]]", clean)   # vớt khối JSON lẫn trong lời dẫn
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    if tra_tho:
        return {"__tho__": clean}
    if stop == "max_tokens":
        raise HTTPException(502, f"AI bị cắt giữa chừng vì chạm trần {max_tokens:,} token "
                                 f"(đã dùng {used}) nên câu trả lời không đọc được. "
                                 f"Rút gọn file rồi thử lại, hoặc tăng trần token.")
    raise HTTPException(502, f"AI trả lời sai định dạng (stop={stop}, {used} token). "
                             f"Nội dung nhận được: {clean[:200] or '(rỗng)'}")


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

    parsed = _goi_ai_json(api_key, model, user_msg, 8000, timeout=180.0, tra_tho=True)
    if "__tho__" in parsed:
        # AI trả không đúng JSON — vẫn đưa nội dung về cho người dùng đọc
        parsed = {"questions": [], "refined_A": parsed["__tho__"],
                  "notes": "AI trả lời không đúng định dạng JSON — nội dung thô ở trên."}
    return {
        "questions": parsed.get("questions") or [],
        "refined_A": parsed.get("refined_A") or "",
        "notes": parsed.get("notes") or "",
    }


@router.post("/api/execute")
def ai_execute(payload: dict = Body(...)):
    """AI THỰC HIỆN đề bài — tạo tool HTML, stream từng đoạn text về client.

    Body: {prompt: "đề bài hoàn chỉnh"}
    Trả về: text/plain stream (toàn bộ trả lời của Claude, client tự tách HTML).
    Stream giữ kết nối sống liên tục nên không vướng timeout proxy của Render.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(503, "Server chưa cấu hình ANTHROPIC_API_KEY "
                                 "(Render → Environment → thêm biến này)")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    # Token suy nghĩ (adaptive thinking) ĐƯỢC TÍNH VÀO max_tokens — để 32000 thì
    # model nghĩ hết phần lớn hạn mức rồi bị cắt giữa chừng khi đang viết file.
    max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "64000"))
    effort = os.getenv("ANTHROPIC_EFFORT", "medium")  # đặt "" để bỏ tham số
    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(422, 'Body thiếu "prompt"')

    user_msg = (prompt + "\n\nQUAN TRỌNG: Trả về TRỰC TIẾP file HTML hoàn chỉnh "
                "(bắt đầu bằng <!DOCTYPE html>, kết thúc bằng </html>), không lời dẫn, "
                "không markdown fence. Nếu đề bài thiếu thông tin thì tự chọn giá trị "
                "hợp lý và ghi chú ngay trong giao diện tool.\n"
                "JavaScript phải đúng cú pháp và chạy được ngay khi mở file bằng trình "
                "duyệt — rà lại trước khi kết thúc: khóa đối tượng động phải bọc ngoặc "
                "vuông ({['Màng '+t]: x} chứ không phải {'Màng '+t: x}), đóng đủ ngoặc "
                "và dấu nháy, không để hàm nào chưa định nghĩa.\n\n"
                "THƯ VIỆN 3D — ĐỌC KỸ: Three.js r128 bản ĐẦY ĐỦ (biến toàn cục THREE) "
                "SẼ ĐƯỢC HỆ THỐNG TỰ ĐỘNG NHÚNG vào file sau khi bạn viết xong. Vì vậy:\n"
                "- TUYỆT ĐỐI KHÔNG tự viết mã thư viện Three.js, KHÔNG dùng CDN, và "
                "KHÔNG được hạ cấp xuống canvas 2D/isometric giả lập với lý do 'giới hạn "
                "offline' — WebGL 3D THẬT là bắt buộc theo chuẩn.\n"
                "- Đặt ĐÚNG một dòng sau vào trong <head>, hệ thống sẽ thay bằng thư viện thật:\n"
                "  <script>/*__SVWS_THREE__*/</script>\n"
                "- Rồi dùng THREE bình thường: THREE.Scene, THREE.WebGLRenderer, "
                "THREE.PerspectiveCamera, THREE.BoxGeometry, THREE.CylinderGeometry…\n"
                "- Kèm theo là thư viện SVWS3D (bộ dựng hình chuẩn của công ty). "
                "DÙNG NÓ, ĐỪNG tự gõ hình học — tự gõ toạ độ sẽ ra bố cục một đường "
                "thẳng, ống đi chéo xuyên thiết bị, tỷ lệ và màu lộn xộn.\n"
                "  Cách dùng (đơn vị mm, trục Y hướng lên):\n"
                "    const S = SVWS3D.scene(document.getElementById('view3d'));\n"
                "    const pos = SVWS3D.layout(EQUIP);   // tự xếp thành hàng có lối đi\n"
                "    EQUIP.forEach(e => S.addEquip(SVWS3D.build(e), pos[e.id], e));\n"
                "    PIPES.forEach(p => S.addPipe(p, pos, EQUIP));\n"
                "    S.fit();                            // camera tự căn, không cắt mép\n"
                "  Bạn CHỈ khai báo dữ liệu, thư viện lo phần vẽ:\n"
                "    EQUIP = [{id,type,tag,name,...kích thước}] — type nhận: tank(d,h,"
                "service,level) · vessel(d,h,material,media,mediaColor) · cartridge(d,h) · "
                "pump · roskid(vessels,memPerVessel,size,rows) · edi · panel(W,H,D) · "
                "dosing(d,h) · uv(d,L) · mixedbed\n"
                "    PIPES = [{from,to,dn,service}] — service nhận: raw · filtered · ro · "
                "di · chem · air · waste · steam · drain (màu tự theo lưu chất, ống tự đi "
                "vuông góc và tự chạy cao hơn thiết bị cao nhất)\n"
                "  Thư viện có sẵn: S.setView('iso'|'front'|'side'|'top'), "
                "S.layer('pipe'|'label'|'equip'|'ground', true/false), S.clear(), "
                "SVWS3D.PALETTE. Vòng lặp vẽ tự chạy — không cần tự viết render loop.\n"
                "  Khi người dùng đổi thông số: gọi S.clear() rồi dựng lại từ EQUIP/PIPES "
                "mới và S.fit() — đó là cách giữ tính parametric.\n"
                "  CHỈ tự viết Three.js thô cho chi tiết mà thư viện chưa có; phần bố cục "
                "và đường ống thì luôn dùng SVWS3D.\n"
                "- Dồn công sức vào MÔ TẢ ĐÚNG dây chuyền: đủ thiết bị theo Phần A, "
                "đúng thứ tự dòng công nghệ, tag thiết bị chuẩn (T-101, P-101, F-101…), "
                "kích thước suy từ thông số thiết kế.\n\n"
                'NÚT "CHỈNH BẢN VẼ BẰNG AI" (mục 3.3 của chuẩn) — làm ĐÚNG như sau:\n'
                "- TUYỆT ĐỐI KHÔNG hỏi người dùng nhập API key và KHÔNG gọi "
                "https://api.anthropic.com (trình duyệt chặn CORS, và để khóa trong file "
                "là lộ khóa cho bất kỳ ai mở file).\n"
                f"- Gọi CỬA NGÕ của công ty: POST {_PUBLIC_URL}/registry/api/claude\n"
                '  Body y hệt dạng Anthropic: {"max_tokens":2000,"messages":[{"role":"user",'
                '"content":"<yêu cầu người dùng + JSON thông số hiện tại + mô tả các trường>"}]}\n'
                "  KHÔNG gửi header x-api-key, KHÔNG gửi anthropic-version — server tự lo khóa.\n"
                "  Đáp án trả về đúng dạng Anthropic: đọc content[0].text (bảo AI trả JSON "
                "thông số đã cập nhật, rồi gán lại vào state và vẽ lại mọi tab).\n"
                "- Lỗi mạng thì báo: 'Cần kết nối mạng để chỉnh bằng AI — các chức năng "
                "còn lại vẫn chạy offline 100%.'")

    def gen():
        # Model suy nghĩ (adaptive thinking) có thể vài phút trước khi viết chữ
        # đầu tiên; Render cắt stream im lặng quá lâu → phải bơm "nhịp tim" (dấu
        # chấm) trong pha suy nghĩ. Client chỉ lấy từ <!DOCTYPE trở đi nên các
        # byte này tự bị loại khi ghép file.
        started_text = False
        last_beat = [datetime.datetime.now(datetime.timezone.utc)]

        def beat():
            """Trả về '.' tối đa 1 lần/2 giây khi chưa có nội dung HTML."""
            now = datetime.datetime.now(datetime.timezone.utc)
            if (now - last_beat[0]).total_seconds() >= 2.0:
                last_beat[0] = now
                return "."
            return ""

        body_json = {"model": model, "max_tokens": max_tokens, "stream": True,
                     "messages": [{"role": "user", "content": user_msg}]}
        if effort:
            body_json["output_config"] = {"effort": effort}

        try:
            with httpx.stream(
                "POST", _ANTHROPIC_URL,
                headers={"x-api-key": api_key,
                         "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json=body_json,
                timeout=httpx.Timeout(1800.0, connect=30.0),
            ) as resp:
                if resp.status_code != 200:
                    body = resp.read().decode("utf-8", "replace")
                    yield "\n[SVWS-LỖI] " + _loi_ai_vn(resp.status_code, body)
                    return
                yield "."  # mở stream ngay để proxy không buffer/timeout
                for line in resp.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        ev = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    etype = ev.get("type")
                    if etype == "content_block_delta":
                        delta = ev.get("delta", {})
                        if delta.get("type") == "text_delta":
                            started_text = True
                            yield delta.get("text", "")
                        elif not started_text:  # thinking_delta… trong pha suy nghĩ
                            hb = beat()
                            if hb:
                                yield hb
                    elif etype == "message_delta":
                        # Luôn đính lý do dừng + số token vào cuối stream để chẩn
                        # đoán được khi file ra thiếu. Client cắt tại </html> nên
                        # dấu này tự biến mất khi file lành lặn.
                        stop = (ev.get("delta") or {}).get("stop_reason")
                        used = (ev.get("usage") or {}).get("output_tokens", "?")
                        if stop == "max_tokens":
                            yield (f"\n[SVWS-LỖI] File bị cắt vì chạm trần {max_tokens:,} token "
                                   f"(đã dùng {used}). Tăng ANTHROPIC_MAX_TOKENS trên Render, "
                                   f"hoặc chia đề bài thành phần nhỏ hơn.")
                            return
                        yield f"\n[SVWS-KET] stop={stop} out={used} tran={max_tokens}"
                    elif etype == "error":
                        yield "\n[SVWS-LỖI] " + _loi_ai_vn(
                            200, json.dumps(ev.get("error", {}), ensure_ascii=False))
                        return
                    elif not started_text:  # ping / content_block_start…
                        hb = beat()
                        if hb:
                            yield hb
        except httpx.HTTPError as e:
            yield f"\n[SVWS-LỖI] Không gọi được Anthropic API: {e}"

    # no-transform: chặn Cloudflare nén gzip (nén sẽ gom buffer làm trễ stream)
    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8",
                             headers={"Cache-Control": "no-cache, no-transform",
                                      "X-Accel-Buffering": "no"})


MAX_SOW_MB = 20


def _docx_text(data: bytes) -> str:
    """Rút chữ từ file .docx (là file zip chứa word/document.xml) — không cần thư viện."""
    import io, zipfile
    from html import unescape
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
    except Exception as e:
        raise ValueError(f"Không mở được file .docx: {e}")
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
    txt = unescape(re.sub(r"<[^>]+>", "", xml))
    return re.sub(r"\n{3,}", "\n\n", txt).strip()


def _xlsx_text(data: bytes) -> str:
    """Đổ bảng Excel thành text để AI đọc (SOW hay kèm bảng thiết bị/thông số)."""
    import io
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(data), data_only=True, read_only=True)
    out = []
    for ws in wb.worksheets:
        out.append(f"--- SHEET: {ws.title} ---")
        for row in ws.iter_rows(values_only=True):
            cells = ["" if c is None else str(c).strip() for c in row]
            if any(cells):
                out.append(" | ".join(cells))
    return "\n".join(out)[:120000]


def _khoi_file(data: bytes, content_type: str, filename: str) -> dict:
    """Dựng khối nội dung gửi Claude từ file người dùng tải lên."""
    import base64
    ct = (content_type or "").lower()
    fn = (filename or "").lower()
    if ct == "application/pdf" or fn.endswith(".pdf"):
        return {"type": "document",
                "source": {"type": "base64", "media_type": "application/pdf",
                           "data": base64.b64encode(data).decode()}}
    if ct.startswith("image/") or fn.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        mt = ct if ct.startswith("image/") else ("image/png" if fn.endswith(".png") else "image/jpeg")
        return {"type": "image",
                "source": {"type": "base64", "media_type": mt,
                           "data": base64.b64encode(data).decode()}}
    if fn.endswith(".docx"):
        return {"type": "text", "text": _docx_text(data)[:120000]}
    if fn.endswith((".xlsx", ".xlsm")):
        return {"type": "text", "text": _xlsx_text(data)}
    if ct.startswith("text/") or fn.endswith((".txt", ".csv", ".md")):
        return {"type": "text", "text": data.decode("utf-8", errors="replace")[:120000]}
    if fn.endswith(".doc"):
        raise ValueError("File .doc là Word đời cũ — mở bằng Word rồi lưu lại thành .docx "
                         "(hoặc in ra PDF) là đọc được.")
    raise ValueError("Định dạng chưa hỗ trợ — dùng PDF, Word (.docx), Excel (.xlsx), "
                     "ảnh (PNG/JPG) hoặc TXT/CSV.")


@router.post("/api/sow")
async def ai_sow(file: UploadFile = File(...)):
    """Đọc file SOW (phạm vi công việc) → soạn sẵn PHIẾU THIẾT KẾ.

    Trả: {design: {...}, questions: [...], tom_tat: "..."}
    Người dùng xem lại rồi mới bấm thêm vào sổ.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(503, "Server chưa cấu hình ANTHROPIC_API_KEY "
                                 "(Render → Environment → thêm biến này)")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

    data = await file.read()
    if not data:
        raise HTTPException(422, "File rỗng")
    if len(data) > MAX_SOW_MB * 1024 * 1024:
        raise HTTPException(413, f"File nặng quá {MAX_SOW_MB}MB — nén lại hoặc tách bớt phần phụ lục.")
    try:
        khoi = _khoi_file(data, file.content_type or "", file.filename or "")
    except ValueError as e:
        raise HTTPException(415, str(e))

    with Session(engine) as s:
        doc = s.get(RegistryDoc, 1)
        d = doc.data if doc else {}
        summary = _sections_summary(d)
        ma_cu = ", ".join((x.get("code") or "") for x in (d.get("designs") or [])[:20])

    sys_msg = (
        "Bạn là kỹ sư trưởng của SVWS (công ty EPC xử lý nước / nước thải / khí thải, TP.HCM). "
        "Người dùng gửi một file SOW (Scope of Work — phạm vi công việc) của dự án. "
        "Hãy ĐỌC KỸ và soạn sẵn một PHIẾU THIẾT KẾ để đưa vào Sổ đăng ký thiết kế.\n\n"
        f"TÓM TẮT CHUẨN 3D DESIGN CỦA CÔNG TY:\n{summary}\n\n"
        f"CÁC MÃ THIẾT KẾ ĐÃ CÓ (đừng trùng): {ma_cu or '(chưa có)'}\n\n"
        "CHỈ trả về JSON hợp lệ, không markdown, không giải thích ngoài JSON:\n"
        '{"design":{"code":"<mã ngắn gọn theo kiểu SVWS-XXX, tự đặt từ nội dung SOW>",'
        '"name":"<tên thiết kế>","tech":"<công nghệ chính>","capacity":"<công suất kèm đơn vị>",'
        '"project":"<tên dự án / khách hàng>",'
        '"params":"<thông số chính, mỗi ý một dòng, gạch đầu dòng>",'
        '"notes":"<yêu cầu riêng / ràng buộc / tiêu chuẩn đầu ra, mỗi ý một dòng>"},'
        '"questions":["<tối đa 6 câu hỏi về thông tin SOW còn thiếu để thiết kế được>"],'
        '"tom_tat":"<2-3 câu tóm tắt phạm vi công việc>"}\n\n'
        "QUY TẮC: KHÔNG bịa số liệu không có trong SOW — thiếu thì để chuỗi rỗng và "
        "nêu thành câu hỏi trong \"questions\". Viết tiếng Việt, ngắn gọn, đúng kỹ thuật."
    )

    parsed = _goi_ai_json(
        api_key, model,
        [khoi, {"type": "text",
                "text": "Đọc SOW này và soạn phiếu thiết kế theo đúng định dạng JSON đã nêu."}],
        16000, system=sys_msg, timeout=420.0)
    dsg = parsed.get("design") or {}
    if not isinstance(dsg, dict) or not (dsg.get("name") or dsg.get("tech")):
        raise HTTPException(502, "AI không rút được nội dung thiết kế từ file này — "
                                 "kiểm tra đúng file SOW chưa.")
    design = {k: str(dsg.get(k) or "") for k in
              ("code", "name", "tech", "capacity", "project", "params", "notes")}
    design["status"] = "Ý tưởng"
    if not design["code"]:
        design["code"] = "SVWS-SOW"
    return {"design": design,
            "questions": [q for q in (parsed.get("questions") or []) if q][:6],
            "tom_tat": parsed.get("tom_tat") or "",
            "nguon": file.filename or ""}


@router.post("/api/claude")
def claude_proxy(payload: dict = Body(...)):
    """Cửa ngõ gọi Claude cho các TOOL sinh ra (nút "Chỉnh bản vẽ bằng AI").

    Tool tải về KHÔNG được ôm API key (lộ khóa cho bất kỳ ai mở file) và cũng
    không gọi thẳng api.anthropic.com được (trình duyệt chặn CORS). Endpoint này
    nhận ĐÚNG dạng body của Anthropic và trả NGUYÊN VĂN đáp án, nên tool chỉ cần
    đổi URL là chạy — không đổi gì khác.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(503, "Server chưa cấu hình ANTHROPIC_API_KEY")
    msgs = payload.get("messages")
    if not isinstance(msgs, list) or not msgs:
        raise HTTPException(422, 'Body thiếu "messages"')

    # CỐ TÌNH bỏ qua "model" do tool gửi lên: tool cũ hay ghim mã model đời cũ đã
    # ngừng phục vụ. Server luôn dùng model hiện hành → tool cũ tự sống lại.
    body = {"model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5"),
            "max_tokens": max(256, min(int(payload.get("max_tokens") or 4000), 8000)),
            "messages": msgs}
    if payload.get("system"):
        body["system"] = payload["system"]
    effort = os.getenv("ANTHROPIC_EFFORT", "medium")
    if effort:
        body["output_config"] = {"effort": effort}
    if len(json.dumps(body)) > 400_000:      # chặn gửi cả file khổng lồ qua đây
        raise HTTPException(413, "Yêu cầu quá lớn — chỉ gửi thông số cần chỉnh, "
                                 "đừng gửi cả nội dung tool.")
    try:
        resp = httpx.post(_ANTHROPIC_URL,
                          headers={"x-api-key": api_key,
                                   "anthropic-version": "2023-06-01",
                                   "content-type": "application/json"},
                          json=body, timeout=300.0)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Không gọi được Anthropic API: {e}")
    if resp.status_code != 200:
        raise HTTPException(502, _loi_ai_vn(resp.status_code, resp.text))
    return resp.json()


@router.post("/api/fix")
def ai_fix(payload: dict = Body(...)):
    """Sửa lỗi cú pháp JS bằng PHÉP THAY THẾ CHUỖI, không chép lại cả file.

    Bắt AI chép lại file 50KB chỉ để sửa một dòng là tự chuốc rủi ro đứt giữa
    chừng; ở đây AI chỉ trả vài trăm ký tự nên nhanh, rẻ và gần như không hỏng.

    Body: {html: "...", error: "Unexpected token '+'"}
    Trả: {replacements: [{old, new}], note}
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(503, "Server chưa cấu hình ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    html = payload.get("html") or ""
    err = (payload.get("error") or "").strip()
    if len(html) < 200:
        raise HTTPException(422, 'Body thiếu "html"')

    user_msg = f"""File HTML dưới đây có LỖI CÚ PHÁP JavaScript nên mở ra trang trắng.
Trình duyệt báo: {err}

Tìm ĐÚNG chỗ sai và trả về các phép thay thế chuỗi TỐI THIỂU để sửa.
Quy tắc bắt buộc:
- "old" phải là đoạn văn bản NGUYÊN VĂN copy từ file, đủ dài để chỉ khớp DUY NHẤT một chỗ.
- "new" là đoạn thay thế đã sửa đúng cú pháp.
- Chỉ sửa lỗi cú pháp, KHÔNG đổi giao diện hay chức năng.
- Lỗi hay gặp: khóa đối tượng động thiếu ngoặc vuông — {{'Màng '+t: x}} phải là {{['Màng '+t]: x}}.

CHỈ trả JSON hợp lệ, không markdown, không giải thích ngoài JSON:
{{"replacements":[{{"old":"...","new":"..."}}],"note":"tóm tắt ngắn chỗ đã sửa"}}

===== FILE =====
{html}"""

    parsed = _goi_ai_json(api_key, model, user_msg, 12000, timeout=300.0)
    reps = [r for r in (parsed.get("replacements") or [])
            if isinstance(r, dict) and r.get("old") and r.get("new") is not None]
    if not reps:
        raise HTTPException(502, "AI không chỉ ra được chỗ cần sửa — làm lại tool từ đầu.")
    return {"replacements": reps, "note": parsed.get("note") or ""}
