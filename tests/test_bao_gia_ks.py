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
