import os
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
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


_HTML = os.path.join(os.path.dirname(__file__), "..", "svws_app.html")
_HUONG_DAN = os.path.join(os.path.dirname(__file__), "..", "huong_dan.html")
_ASSETS = os.path.join(os.path.dirname(__file__), "assets")


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


# PWA: manifest + icon để "Thêm vào màn hình chính" trên điện thoại
# cài như app thật (icon riêng, chạy toàn màn hình).
@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse(
        {
            "name": "SVWS — Hệ thống quản trị",
            "short_name": "SVWS",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#EAF1F5",
            "theme_color": "#0F2C44",
            "icons": [
                {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
                {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png",
                 "purpose": "maskable"},
            ],
        },
        media_type="application/manifest+json",
        headers=_NO_CACHE,
    )


@app.get("/icon-192.png")
def icon_192():
    return FileResponse(os.path.join(_ASSETS, "icon-192.png"), media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/icon-512.png")
def icon_512():
    return FileResponse(os.path.join(_ASSETS, "icon-512.png"), media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/health")
def health():
    return {"he_thong": "SVWS",
            "modules": ["kho", "ncc", "du_an", "ban_hang", "ke_toan",
                        "tai_chinh", "nhan_su", "cho_thue", "crm"],
            "trang_thai": "ok"}
