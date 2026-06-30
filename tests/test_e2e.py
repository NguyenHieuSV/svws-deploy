"""
Test đầu-cuối xuyên các module trên DB thật. Yêu cầu: `make db-up` + `make seed`.
Mỗi lần chạy dùng mã ngẫu nhiên nên re-runnable.
"""
import os
import uuid
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://svws:svws@localhost:5432/svws")

try:
    from sqlalchemy import create_engine
    create_engine(os.environ["DATABASE_URL"]).connect().close()
    from fastapi.testclient import TestClient
    from app.main import app
    _client = TestClient(app)
except Exception as e:  # noqa
    pytest.skip(f"Cần DB đang chạy: {e}", allow_module_level=True)


def _tok(email):
    r = _client.post("/auth/login", data={"username": email, "password": "matkhau123"})
    assert r.status_code == 200, "Chưa seed user? chạy `make seed`"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_luong_rbac_va_lien_thong():
    sfx = uuid.uuid4().hex[:6]
    H = {r: _tok(f"{e}@svws.vn") for r, e in {
        "ceo": "ceo", "thukho": "thukho", "nvkd": "nvkd", "tpkd": "tpkd"}.items()}

    # Kho: THUKHO tạo hàng + nhập; NV_KD bị chặn
    hh = _client.post("/kho/hang-hoa", headers=H["thukho"],
                      json={"ma": f"H-{sfx}", "ten": "Bơm", "loai": "THIET_BI", "ton_min": 5}).json()["id"]
    assert _client.post("/kho/hang-hoa", headers=H["nvkd"],
                        json={"ten": "x", "loai": "VAT_TU"}).status_code == 403
    _client.post("/kho/phieu", headers=H["thukho"],
                 json={"loai": "NHAP", "chi_tiet": [{"hang_hoa_id": hh, "so_luong": 500}]})

    # Bán hàng: duyệt theo hạn mức (TP_KD ≤100tr)
    kh = _client.post("/ban-hang/khach-hang", headers=H["nvkd"],
                      json={"ma": f"K-{sfx}", "ten": "KH test"}).json()["id"]
    bg80 = _client.post("/ban-hang/bao-gia", headers=H["nvkd"],
                        json={"khach_hang_id": kh, "chi_tiet": [{"hang_hoa_id": hh, "so_luong": 8, "don_gia": 10_000_000}]}).json()["id"]
    bg150 = _client.post("/ban-hang/bao-gia", headers=H["nvkd"],
                         json={"khach_hang_id": kh, "chi_tiet": [{"hang_hoa_id": hh, "so_luong": 15, "don_gia": 10_000_000}]}).json()["id"]
    assert _client.post(f"/ban-hang/bao-gia/{bg80}/duyet", headers=H["tpkd"]).status_code == 200
    assert _client.post(f"/ban-hang/bao-gia/{bg150}/duyet", headers=H["tpkd"]).status_code == 403  # >100tr
    assert _client.post(f"/ban-hang/bao-gia/{bg150}/duyet", headers=H["ceo"]).status_code == 200

    # Liên thông: tạo đơn -> xuất kho -> hóa đơn + công nợ
    dh = _client.post(f"/ban-hang/bao-gia/{bg80}/tao-don", headers=H["nvkd"]).json()["id"]
    xk = _client.post(f"/ban-hang/don-hang/{dh}/xuat-kho", headers=H["nvkd"])
    assert xk.status_code == 200 and xk.json()["hoa_don_id"]


def test_luong_quy_trinh_tuan_tu():
    H = {r: _tok(f"{e}@svws.vn") for r, e in {
        "ceo": "ceo", "ktt": "ktt", "nvhcns": "nvhcns"}.items()}
    thang = "2026-05"
    assert _client.post("/nhan-su/tinh-luong", headers=H["nvhcns"], json={"thang": thang}).status_code == 200
    assert _client.post(f"/nhan-su/bang-luong/{thang}/duyet-ktt", headers=H["nvhcns"]).status_code == 403  # sai vai trò
    assert _client.post(f"/nhan-su/bang-luong/{thang}/ky-ceo", headers=H["ceo"]).status_code == 400        # sai thứ tự
    assert _client.post(f"/nhan-su/bang-luong/{thang}/duyet-ktt", headers=H["ktt"]).status_code == 200
    assert _client.post(f"/nhan-su/bang-luong/{thang}/ky-ceo", headers=H["ceo"]).status_code == 200
