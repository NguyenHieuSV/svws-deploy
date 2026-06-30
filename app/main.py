import os
from fastapi import FastAPI
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


_HTML = os.path.join(os.path.dirname(__file__), "..", "svws_app.html")


@app.get("/")
def goc():
    if os.path.exists(_HTML):
        return FileResponse(_HTML, media_type="text/html; charset=utf-8")
    return {"he_thong": "SVWS", "trang_thai": "ok"}


@app.get("/health")
def health():
    return {"he_thong": "SVWS",
            "modules": ["kho", "ncc", "du_an", "ban_hang", "ke_toan",
                        "tai_chinh", "nhan_su", "cho_thue", "crm"],
            "trang_thai": "ok"}
