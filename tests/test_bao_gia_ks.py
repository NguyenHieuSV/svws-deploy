"""
📋/📉 Kiểm soát báo giá ↔ dự toán (28/10/2026): bắt buộc có dự toán đủ dòng + giá; biên so với dự toán;
cổng trình duyệt / duyệt / gửi (người thường bị chặn, CEO phải xác nhận). Dự toán được thay bằng dữ liệu giả.
"""
import pytest
from fastapi import HTTPException

from app import bao_gia_ks as bk
from app.config import settings


class _Bgf:
    def __init__(self, so, items, **kw):
        self.so = so
        self.noi_dung = dict({"so": so, "items": items, "vat_pct": 8}, **kw)


class _Nd:
    def __init__(self, ma):
        self.vai_tro = type("VT", (), {"ma": ma})()


DT = {
    "DA-X-1026": {"loai": "DTB", "id": 1, "ma": "DA-X-1026", "so_dong": 3, "dong_thieu_gia": [], "tong": 80e6},
    "TM-Y-1026": {"loai": "DTB", "id": 2, "ma": "TM-Y-1026", "so_dong": 2, "dong_thieu_gia": ["Bơm 5HP"], "tong": 10e6},
    "DA-Z-1026": {"loai": "BOQ", "id": 3, "ma": "DA-Z-1026", "so_dong": 0, "dong_thieu_gia": [], "tong": 0},
}


@pytest.fixture(autouse=True)
def _gia(monkeypatch):
    monkeypatch.setattr(bk, "tim_du_toan", lambda db, bgf: DT.get(bgf.so))
    monkeypatch.setattr(settings, "bg_bien_toi_thieu", 15.0)
    monkeypatch.setattr(settings, "bg_bien_goi_y", 20.0)


def _it(sl, dg):
    return {"ten": "x", "so_luong": sl, "don_gia": dg}


def test_kiem_tra():
    k = bk.kiem_tra(None, _Bgf("DA-X-1026", [_it(1, 100e6)]))                 # 100 vs 80 → biên 20% ✓
    assert k["thieu_du_toan"] is None and k["bien"] == 20.0 and k["canh_bao_bien"] is None
    k = bk.kiem_tra(None, _Bgf("DA-X-1026", [_it(1, 90e6)]))                  # 90 vs 80 → biên 11,1% < 15%
    assert k["bien"] == 11.1 and "biên chỉ 11,1%" in k["canh_bao_bien"]
    k = bk.kiem_tra(None, _Bgf("DA-X-1026", [_it(1, 70e6)]))                  # lỗ
    assert "LỖ" in k["canh_bao_bien"]
    k = bk.kiem_tra(None, _Bgf("DA-X-1026", [], dinh_kem_ten="Proposal.pdf")) # báo giá theo file → không so được
    assert "không có dòng giá" in k["canh_bao_bien"]
    assert "CHƯA CÓ DỰ TOÁN" in bk.kiem_tra(None, _Bgf("TM-KHONG-1026", [_it(1, 5e6)]))["thieu_du_toan"]
    assert "CHƯA CÓ ĐƠN GIÁ" in bk.kiem_tra(None, _Bgf("TM-Y-1026", [_it(1, 5e6)]))["thieu_du_toan"]
    assert "chưa có dòng" in bk.kiem_tra(None, _Bgf("DA-Z-1026", [_it(1, 5e6)]))["thieu_du_toan"]


def test_cong():
    tot, thieu, thap = _Bgf("DA-X-1026", [_it(1, 100e6)]), _Bgf("TM-KHONG-1026", [_it(1, 5e6)]), _Bgf("DA-X-1026", [_it(1, 90e6)])
    bk.cong(None, tot, _Nd("NV_KD"), False, "trình duyệt")                     # đủ dự toán → qua
    with pytest.raises(HTTPException) as e:
        bk.cong(None, thieu, _Nd("ADMIN"), True, "trình duyệt")                 # thiếu dự toán: người thường bị chặn
    assert e.value.status_code == 400 and "📋" in e.value.detail
    with pytest.raises(HTTPException) as e:
        bk.cong(None, thieu, _Nd("CEO"), False, "trình duyệt")                  # CEO: hỏi xác nhận
    assert e.value.status_code == 409
    assert bk.cong(None, thieu, _Nd("CEO"), True, "trình duyệt")["vuot"]        # CEO xác nhận → qua, ghi vết
    bk.cong(None, thap, _Nd("NV_KD"), False, "trình duyệt")                     # biên thấp không chặn lúc trình duyệt
    with pytest.raises(HTTPException) as e:
        bk.cong(None, thap, _Nd("ADMIN"), True, "duyệt", kiem_bien=True)       # lúc duyệt: chỉ CEO
    assert e.value.status_code == 403 and "📉" in e.value.detail
    with pytest.raises(HTTPException) as e:
        bk.cong(None, thap, _Nd("CEO"), False, "duyệt", kiem_bien=True)
    assert e.value.status_code == 409
    assert bk.cong(None, thap, _Nd("CEO"), True, "duyệt", kiem_bien=True)["vuot"]


def test_san_bien_theo_nhom(monkeypatch):
    monkeypatch.setattr(settings, "bg_bien_thiet_bi", 15.0); monkeypatch.setattr(settings, "bg_bien_vat_tu", 25.0)
    monkeypatch.setattr(settings, "bg_bien_nhan_cong", 30.0); monkeypatch.setattr(settings, "bg_chi_phi_chung", 5.0)
    nd = {"chi_phi_chung": 5, "items": [
        {"ten": "Bơm", "nhom": "THIET_BI", "so_luong": 1, "gia_von": 100e6, "don_gia": 124e6},     # vốn đầy 105 → biên 15,3% ✓
        {"ten": "Ống", "nhom": "VAT_TU", "so_luong": 10, "gia_von": 1e6, "don_gia": 1.3e6},        # 1,05/1,3 → 19,2% < 25 ✗
        {"ten": "Lắp", "nhom": "NHAN_CONG", "so_luong": 1, "gia_von": 0, "don_gia": 5e6},          # không giá vốn → không xét
        {"ten": "Bỏ", "nhom": "VAT_TU", "so_luong": 0, "gia_von": 1e6, "don_gia": 1},             # SL 0 → không xét
    ]}
    ds = bk.dong_duoi_san(nd)
    assert [x["ten"] for x in ds] == ["Ống"] and ds[0]["bien"] == 19.2 and ds[0]["san"] == 25.0
    with pytest.raises(HTTPException) as e:
        bk.chan_duoi_san(nd, _Nd("NV_KD"))
    assert e.value.status_code == 403 and "DƯỚI SÀN" in e.value.detail and "19,2% < sàn 25%" in e.value.detail
    bk.chan_duoi_san(nd, _Nd("ADMIN"))                 # CEO / Admin được dưới sàn
    bk.chan_duoi_san(nd, _Nd("CEO"))
    nd["items"][1]["don_gia"] = 1.4e6                  # 1,05/1,4 → 25% = sàn → đạt
    assert bk.dong_duoi_san(nd) == []
    bk.chan_duoi_san(nd, _Nd("NV_KD"))
