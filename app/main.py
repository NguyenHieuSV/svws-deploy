import os
from fastapi import FastAPI, Request
from training import router as training_router
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import (auth, kho, ncc, du_an, ban_hang, ke_toan, tai_chinh,
                      nhan_su, cho_thue, crm, ban_hang_ext, ke_toan_quy, vay, quy_trich_lap,
                      cau_hinh, nhan_su_kpi, cho_thue_ops, dich_vu_kt, quet_mail,
                      doc_anh_bcvh)
from svws_registry import registry

app = FastAPI(title="SVWS — Backend hợp nhất (9 module nghiệp vụ)")
app.include_router(training_router)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)
for r in (auth, kho, ncc, du_an, ban_hang, ke_toan, tai_chinh, nhan_su, cho_thue, crm, ban_hang_ext, ke_toan_quy, vay, quy_trich_lap, cau_hinh, nhan_su_kpi, cho_thue_ops, dich_vu_kt, quet_mail,
                      doc_anh_bcvh):
    app.include_router(r.router)
app.include_router(registry.router)


@app.on_event("startup")
def _bat_scheduler():
    """Bật luồng nền gửi bản tin nhắc việc. Lỗi ở đây KHÔNG được chặn app khởi động."""
    try:
        from .scheduler import khoi_dong
        khoi_dong()
    except Exception as e:
        print(f"[SCHEDULER] Không bật được: {type(e).__name__}: {e}")


@app.on_event("startup")
def _bo_de_xuat_mua():
    """Chuyển đổi dữ liệu MỘT LẦN khi bỏ mục Đề xuất mua hàng (10/10/2026). Lỗi KHÔNG chặn app khởi động."""
    try:
        from .bo_de_xuat_mua import chay_mot_lan
        chay_mot_lan()
    except Exception as e:
        print(f"[BO_DE_XUAT] Không chạy được: {type(e).__name__}: {e}")


@app.on_event("startup")
def _init_registry():
    """Tạo bảng + nạp seed Rev.E cho Design Registry. Lỗi KHÔNG chặn app khởi động."""
    try:
        registry.init_db()
    except Exception as e:
        print(f"[REGISTRY] Không khởi tạo được DB: {type(e).__name__}: {e}")


_HTML = os.path.join(os.path.dirname(__file__), "..", "svws_app.html")
_HUONG_DAN = os.path.join(os.path.dirname(__file__), "..", "huong_dan.html")
_SO_TAY = os.path.join(os.path.dirname(__file__), "..", "so_tay_quy_che.docx")
_QC_TOAN_VAN = os.path.join(os.path.dirname(__file__), "..", "quy_che_toan_van.json")   # sinh bằng scripts/tach_quy_che.py
_qc_tv_nho = {"mtime": None, "data": {}}
_CHUP_ANH = os.path.join(os.path.dirname(__file__), "..", "static", "chup-anh.html")


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


@app.get("/chup-anh")
def chup_anh():
    """Trang điện thoại: chụp ảnh hiện trường → AI điền Báo cáo vận hành (Cho thuê)."""
    if os.path.exists(_CHUP_ANH):
        return FileResponse(_CHUP_ANH, media_type="text/html; charset=utf-8", headers=_NO_CACHE)
    return {"he_thong": "SVWS", "trang_thai": "chua co trang chup anh"}


# --- Cài "BCVH SVWS" như app trên điện thoại (PWA): manifest, icon, service worker ---
_PWA_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "pwa")
_PWA_TEP = {"manifest.webmanifest": "application/manifest+json",
            "icon-192.png": "image/png", "icon-512.png": "image/png",
            "icon-maskable-512.png": "image/png", "apple-touch-icon.png": "image/png"}


@app.get("/chup-anh/{ten}")
def chup_anh_pwa(ten: str):
    if ten not in _PWA_TEP:
        from fastapi import HTTPException
        raise HTTPException(404, "Không có tệp này")
    return FileResponse(os.path.join(_PWA_DIR, ten), media_type=_PWA_TEP[ten],
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/chup-anh-sw.js")
def chup_anh_sw():
    """Service worker đặt ở gốc site để đăng ký scope '/chup-anh' (trang không có dấu / cuối)."""
    return FileResponse(os.path.join(_PWA_DIR, "sw.js"), media_type="text/javascript; charset=utf-8",
                        headers=_NO_CACHE)


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


@app.get("/quy-che/toan-van/{ma_so}")
def quy_che_toan_van(ma_so: str):
    """Toàn văn MỘT quy chế (HTML gọn) cho tab Tổng quan › Quy chế công ty — cùng nội dung với Sổ tay Word tải về.
    Công khai như /so-tay-quy-che (quy chế phổ biến cho mọi người lao động); đọc file JSON sinh sẵn, nhớ theo mtime."""
    import json
    from fastapi import HTTPException
    try:
        mt = os.path.getmtime(_QC_TOAN_VAN)
        if _qc_tv_nho["mtime"] != mt:
            with open(_QC_TOAN_VAN, encoding="utf-8") as f:
                _qc_tv_nho["data"] = json.load(f)
            _qc_tv_nho["mtime"] = mt
    except (OSError, ValueError):
        raise HTTPException(404, "Chưa có toàn văn quy chế trên máy chủ")
    vb = (_qc_tv_nho["data"].get("van_ban") or {}).get(ma_so)
    if vb is None:
        raise HTTPException(404, "Không có văn bản này")
    return vb


def _luu_chat_dm(d: dict):
    """Ghi nhớ phòng nhắn riêng (DM) của người vừa nhắn bot, để LẦN SAU gửi thẳng
    vào phòng đó — né được giới hạn Service Account không tra người dùng qua email."""
    u = d.get("user") or (d.get("message") or {}).get("sender") or {}
    sp = d.get("space") or (d.get("message") or {}).get("space") or {}
    uid = u.get("name")                      # "users/1234567890"
    space = sp.get("name")                   # "spaces/AAAA..."
    if not uid:
        return
    from .database import SessionLocal
    from .models import ChatDM
    db = SessionLocal()
    try:
        r = db.get(ChatDM, uid)
        if r is None:
            r = ChatDM(user_id=uid)
            db.add(r)
        if u.get("email"):
            r.google_email = u.get("email")
        if u.get("displayName"):
            r.ten_hthi = u.get("displayName")
        # chỉ lưu space của phòng nhắn riêng 1-1 (DM), bỏ qua phòng nhóm
        if space and (sp.get("type") in (None, "DM", "DIRECT_MESSAGE") or sp.get("singleUserBotDm")):
            r.space_name = space
        db.commit()
    finally:
        db.close()


@app.post("/google-chat/events")
async def google_chat_events(request: Request):
    """Địa chỉ nhận sự kiện của Chat app “Nhắc việc SVWS”.

    Bot chỉ GỬI lời nhắc, không xử lý hội thoại. Endpoint này tồn tại vì Google
    Workspace Marketplace BẮT BUỘC Chat app phải khai báo một địa chỉ nhận sự kiện.

    Khi ai đó nhắn bot lần đầu, ta LƯU LẠI phòng nhắn riêng của họ (không đọc nội
    dung tin) rồi chào lại. Nhờ vậy về sau bot gửi lời nhắc thẳng vào phòng đó.
    """
    try:
        d = await request.json()
    except Exception:
        d = {}
    loai = (d.get("type") or "").upper()
    try:
        _luu_chat_dm(d)
    except Exception as e:
        print(f"[CHAT-EVENT] Không lưu được DM: {type(e).__name__}: {e}")
    if loai in ("ADDED_TO_SPACE", "MESSAGE"):
        return {"text": ("Xin chào! Đây là bot nhắc việc của hệ thống SVWS. ✅\n"
                         "Từ giờ bot có thể gửi lời nhắc công việc riêng cho bạn.\n"
                         "Bạn không cần trả lời tin này — xem và đánh dấu hoàn thành "
                         "trong app: Working time & Report → Work Reminder.")}
    return {}


@app.get("/health")
def health():
    return {"he_thong": "SVWS",
            "modules": ["kho", "ncc", "du_an", "ban_hang", "ke_toan",
                        "tai_chinh", "nhan_su", "cho_thue", "crm"],
            "trang_thai": "ok"}
