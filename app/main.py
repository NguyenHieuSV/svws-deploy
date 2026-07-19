import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import (auth, kho, ncc, du_an, ban_hang, ke_toan, tai_chinh,
                      nhan_su, cho_thue, crm, ban_hang_ext, ke_toan_quy, vay, quy_trich_lap,
                      cau_hinh, nhan_su_kpi, cho_thue_ops)

app = FastAPI(title="SVWS — Backend hợp nhất (9 module nghiệp vụ)")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)
for r in (auth, kho, ncc, du_an, ban_hang, ke_toan, tai_chinh, nhan_su, cho_thue, crm, ban_hang_ext, ke_toan_quy, vay, quy_trich_lap, cau_hinh, nhan_su_kpi, cho_thue_ops):
    app.include_router(r.router)


@app.on_event("startup")
def _bat_scheduler():
    """Bật luồng nền gửi bản tin nhắc việc. Lỗi ở đây KHÔNG được chặn app khởi động."""
    try:
        from .scheduler import khoi_dong
        khoi_dong()
    except Exception as e:
        print(f"[SCHEDULER] Không bật được: {type(e).__name__}: {e}")


_HTML = os.path.join(os.path.dirname(__file__), "..", "svws_app.html")
_HUONG_DAN = os.path.join(os.path.dirname(__file__), "..", "huong_dan.html")
_SO_TAY = os.path.join(os.path.dirname(__file__), "..", "so_tay_quy_che.docx")


# no-cache: trình duyệt phải hỏi lại server mỗi lần mở (ETag 304 nếu chưa đổi)
# -> người dùng luôn nhận bản mới nhất ngay sau khi deploy, khỏi Ctrl+F5.
_NO_CACHE = {"Cache-Control": "no-cache"}


@app.get("/")
def goc():
    if os.path.exists(_HTML):
        return FileResponse(_HTML, media_type="text/html; charset=utf-8",
                            headers=_NO_CACHE)
    return {"he_thong": "SVWS", "trang_thai": "ok"}


@app.get("/huong-dan")
def huong_dan():
    if os.path.exists(_HUONG_DAN):
        return FileResponse(_HUONG_DAN, media_type="text/html; charset=utf-8",
                            headers=_NO_CACHE)
    return {"he_thong": "SVWS", "trang_thai": "chua co huong dan"}


@app.get("/so-tay-quy-che")
def so_tay_quy_che():
    """Tải Sổ tay quy chế công ty (bản Word) cho mọi người tham khảo."""
    if os.path.exists(_SO_TAY):
        return FileResponse(
            _SO_TAY,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="So tay quy che cong ty - Song Viet.docx",
            headers=_NO_CACHE)
    return {"he_thong": "SVWS", "trang_thai": "chua co so tay quy che"}


@app.post("/google-chat/events")
async def google_chat_events(request: Request):
    """Địa chỉ nhận sự kiện của Chat app “Nhắc việc SVWS”.

    Bot chỉ GỬI lời nhắc, không xử lý hội thoại. Endpoint này tồn tại vì Google
    Workspace Marketplace BẮT BUỘC Chat app phải khai báo một địa chỉ nhận sự kiện
    (không khai thì không bật được “Standalone Chat App”).

    Nó chỉ chào lại để người dùng biết bot đã sẵn sàng — không đọc, không lưu,
    không hành động gì với nội dung tin nhắn.
    """
    try:
        d = await request.json()
    except Exception:
        d = {}
    loai = (d.get("type") or "").upper()
    if loai in ("ADDED_TO_SPACE", "MESSAGE"):
        return {"text": ("Xin chào! Đây là bot nhắc việc của hệ thống SVWS.\n"
                         "Bot sẽ tự gửi lời nhắc công việc và bản tin đầu ngày cho bạn — "
                         "bạn không cần trả lời tin này.\n"
                         "Xem và đánh dấu hoàn thành trong app: "
                         "Working time & Report → Work Reminder.")}
    return {}


@app.get("/health")
def health():
    return {"he_thong": "SVWS",
            "modules": ["kho", "ncc", "du_an", "ban_hang", "ke_toan",
                        "tai_chinh", "nhan_su", "cho_thue", "crm"],
            "trang_thai": "ok"}
