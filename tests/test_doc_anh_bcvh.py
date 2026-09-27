"""
Test đọc ảnh hiện trường → BCVH (Cho thuê). Không gọi AI thật: thay ai_gateway.doc_anh_bcvh
bằng kết quả giả lập, kiểm phần hậu xử lý (khớp danh mục + cảnh báo) và luồng lưu qua endpoint cũ.
Yêu cầu: `make db-up` + `make seed`.
"""
import io
import os
import uuid
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://svws:svws@localhost:5432/svws")

try:
    from sqlalchemy import create_engine
    create_engine(os.environ["DATABASE_URL"]).connect().close()
    from fastapi.testclient import TestClient
    from app.main import app
    from app import ai_gateway
    from app.config import settings
    _client = TestClient(app)
except Exception as e:  # noqa
    pytest.skip(f"Cần DB đang chạy: {e}", allow_module_level=True)


def _tok(email):
    r = _client.post("/auth/login", data={"username": email, "password": "matkhau123"})
    assert r.status_code == 200, "Chưa seed user? chạy `make seed`"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _anh(n=1):
    # 1x1 JPEG hợp lệ tối thiểu — AI bị thay bằng hàm giả nên nội dung không quan trọng
    jpg = bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffd9")
    return [("files", (f"a{i}.jpg", io.BytesIO(jpg), "image/jpeg")) for i in range(n)]


@pytest.fixture()
def du_an():
    H = _tok("ceo@svws.vn")
    sfx = uuid.uuid4().hex[:6]
    ts = _client.post("/cho-thue/tai-san", headers=H,
                      json={"ma": f"CT-ANH-{sfx}", "ten": "XLNT 110 m3/ngày", "loai": "HE_THONG"}).json()["id"]
    for ct in [{"loai": "KY_THUAT", "vi_tri": "Sau DAF", "chi_tieu": "COD (mg/l)", "don_vi": "mg/l"},
               {"loai": "KY_THUAT", "vi_tri": "Bể điều hòa", "chi_tieu": "COD (mg/l)", "don_vi": "mg/l"},
               {"loai": "HOA_CHAT_VT", "chi_tieu": "PAC 10%", "don_vi": "Kg"},
               {"loai": "KHOI_LUONG", "chi_tieu": "Đồng hồ đầu vào", "don_vi": "m3"}]:
        assert _client.post(f"/cho-thue/tai-san/{ts}/chi-tieu", headers=H, json=ct).status_code == 201
    # dữ liệu cũ để so sánh
    _client.post(f"/cho-thue/tai-san/{ts}/bao-cao-kt", headers=H, json={"ngay": "2026-09-25", "dong": [
        {"vi_tri": "Sau DAF", "chi_tieu": "COD (mg/l)", "ket_qua": "112"},
        {"vi_tri": "Bể điều hòa", "chi_tieu": "COD (mg/l)", "ket_qua": "1020"}]})
    _client.post(f"/cho-thue/tai-san/{ts}/bao-cao-hc", headers=H, json={"ngay": "2026-09-15", "dong": [
        {"ten": "PAC 10%", "luong_nhap": 10100, "luong_ton": 12000, "don_vi": "Kg"}]})
    _client.post(f"/cho-thue/tai-san/{ts}/bao-cao-kl", headers=H, json={"ngay": "2026-09-25", "dong": [
        {"he_thong": "Đồng hồ đầu vào", "chi_so": 5000, "don_vi": "m3"}]})
    return ts, H


def test_doc_anh_hau_xu_ly_va_luu(du_an, monkeypatch):
    ts, H = du_an
    monkeypatch.setattr(settings, "anthropic_api_key", "test")

    def gia(anh, mau, ngay, goi_y):
        assert len(anh) == 3 and goi_y[0] == "Sau DAF"
        assert any(c["chi_tieu"] == "COD (mg/l)" for c in mau["ky_thuat"])
        return {
            "anh": [{"so": 1, "loai": "may_do_cam_tay", "mo_ta": "Palintest COD"},
                    {"so": 2, "loai": "phieu_giao_hang", "mo_ta": "An Phú"},
                    {"so": 3, "loai": "dong_ho_tong", "mo_ta": "Đồng hồ"}],
            "ky_thuat": [
                {"anh": 1, "ngay": "2026-09-27", "vi_tri": "sau daf", "chi_tieu": "cod (MG/L)", "ket_qua": "70", "tin_cay": "cao"},
                {"anh": 1, "ngay": "2026-09-27", "vi_tri": "Bể điều hòa", "chi_tieu": "COD (mg/l)", "ket_qua": "015", "tin_cay": "tb", "ly_do": "mờ"}],
            "hoa_chat": [{"anh": 2, "ngay": "2026-09-15", "ten": "pac 10%", "luong_nhap": 10100, "luong_ton": None}],
            "khoi_luong": [{"anh": 3, "ngay": "2026-09-27", "he_thong": "Đồng hồ đầu vào", "chi_so": 4990}],
        }
    monkeypatch.setattr(ai_gateway, "doc_anh_bcvh", gia)

    r = _client.post(f"/cho-thue/tai-san/{ts}/doc-anh", headers=H, files=_anh(3),
                     data={"ngay": "2026-09-27", "goi_y": '["Sau DAF","",""]'})
    assert r.status_code == 200, r.text
    kq = r.json()
    kt = kq["ky_thuat"]
    # khớp tên theo danh mục (hoa thường / dấu)
    assert kt[0]["vi_tri"] == "Sau DAF" and kt[0]["chi_tieu"] == "COD (mg/l)" and kt[0]["trong_mau"]
    assert kt[0]["don_vi"] == "mg/l" and kt[0]["lan_truoc"]["ket_qua"] == "112"
    # 70 so với 112 = -37% → không cảnh báo lệch
    assert not any("Lệch" in c["noi_dung"] for c in kt[0]["canh_bao"])
    # "015" so với 1020 → cảnh báo số 0 đầu + lệch
    nd = " ".join(c["noi_dung"] for c in kt[1]["canh_bao"])
    assert "bắt đầu bằng 0" in nd and "Lệch" in nd and "Nên xem lại" in nd
    hc = kq["hoa_chat"][0]
    assert hc["ten"] == "PAC 10%" and hc["don_vi"] == "Kg"
    assert any(c["muc"] == "bad" and "trùng phiếu" in c["noi_dung"] for c in hc["canh_bao"])
    assert any("TỒN CUỐI NGÀY" in c["noi_dung"] for c in hc["canh_bao"])
    kl = kq["khoi_luong"][0]
    assert kl["lan_truoc"]["chi_so"] == 5000
    assert any(c["muc"] == "bad" and "NHỎ HƠN" in c["noi_dung"] for c in kl["canh_bao"])
    assert kq["anh"][1]["loai"] == "phieu_giao_hang"

    # lưu qua endpoint cũ như trang /chup-anh làm
    assert _client.post(f"/cho-thue/tai-san/{ts}/bao-cao-kt", headers=H, json={"ngay": "2026-09-27", "dong": [
        {"vi_tri": kt[0]["vi_tri"], "chi_tieu": kt[0]["chi_tieu"], "ket_qua": "70"}]}).status_code == 201
    ds = _client.get(f"/cho-thue/tai-san/{ts}/bao-cao?loai=KY_THUAT", headers=H).json()
    assert any(x["ngay"] == "2026-09-27" and x["thong_so"] == "70" and x["vi_tri"] == "Sau DAF" for x in ds)


def test_doc_anh_chua_cau_hinh_ai(du_an, monkeypatch):
    ts, H = du_an
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    r = _client.post(f"/cho-thue/tai-san/{ts}/doc-anh", headers=H, files=_anh(1))
    assert r.status_code == 502 and "ANTHROPIC_API_KEY" in r.json()["detail"]


def test_doc_anh_chan_quyen_va_gioi_han(du_an):
    ts, H = du_an
    assert _client.post(f"/cho-thue/tai-san/{ts}/doc-anh", headers=_tok("nvkd@svws.vn"),
                        files=_anh(1)).status_code == 403
    assert _client.post(f"/cho-thue/tai-san/{ts}/doc-anh", headers=H, files=_anh(11)).status_code == 400
    assert _client.get(f"/cho-thue/tai-san/{ts}/mau-bcvh", headers=H).json()["hoa_chat"][0]["ten"] == "PAC 10%"


def test_trang_chup_anh():
    r = _client.get("/chup-anh")
    assert r.status_code == 200 and "Chụp ảnh" in r.text and "/doc-anh" in r.text


def test_cai_app_pwa():
    m = _client.get("/chup-anh/manifest.webmanifest")
    assert m.status_code == 200 and m.json()["display"] == "standalone"
    for ic in m.json()["icons"]:
        assert _client.get(ic["src"]).status_code == 200
    assert _client.get("/chup-anh/apple-touch-icon.png").status_code == 200
    assert _client.get("/chup-anh-sw.js").headers["content-type"].startswith("text/javascript")
    assert _client.get("/chup-anh/khong-co.txt").status_code == 404
    assert 'rel="manifest"' in _client.get("/chup-anh").text
