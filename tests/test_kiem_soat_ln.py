"""
📉 Kiểm soát lợi nhuận theo nhóm mã (27/10/2026): phép đánh giá cờ + cổng duyệt PO (chỉ CEO, phải xác nhận)
+ bản tuần. Số liệu nhóm được thay bằng bảng giả (công thức chi phí thật đã có test riêng ở Kiểm soát).
"""
from datetime import date

import pytest
from fastapi import HTTPException

from app import kiem_soat_ln as ks
from app.config import settings

NHOM = {  # nhóm gốc + tháng → doanh thu / chi phí (gồm VAT)
    "DV-COA-NT-1026": {"dt": 0.0, "cp": 20e6, "dau_tu": False, "ma": []},          # tháng này chưa ghi doanh thu
    "DV-COA-NT-0926": {"dt": 200e6, "cp": 120e6, "dau_tu": False, "ma": []},
    "TM-SIC-1026": {"dt": 100e6, "cp": 80e6, "dau_tu": False, "ma": []},
    "TM-HEI-0326": {"dt": 0.0, "cp": 136e6, "dau_tu": False, "ma": []},
    "DV-COA-RO-2024": {"dt": 0.0, "cp": 500e6, "dau_tu": True, "ma": []},
}


@pytest.fixture(autouse=True)
def _gia(monkeypatch):
    monkeypatch.setattr(ks, "so_lieu_nhom", lambda db, nh: NHOM.get(nh, {"dt": 0.0, "cp": 0.0, "dau_tu": False, "ma": []}))
    monkeypatch.setattr(settings, "po_bien_ln_toi_thieu", 15.0)


def test_mien_kiem_va_nhom():
    assert ks.mien_kiem("OP-SV-1026") and ks.mien_kiem("KHO") and ks.mien_kiem("") and ks.mien_kiem("DV-COA-RO-2024")
    assert not ks.mien_kiem("DV-COA-NT-1026-02")
    assert ks.nhom_cua("DV-COA-NT-1026-02") == "DV-COA-NT-1026"
    assert ks.nhom_thang_truoc("DV-COA-NT-0126") == "DV-COA-NT-1225"


def test_danh_gia():
    assert ks.danh_gia(None, "OP-SV-1026", 50e6) is None                         # chi phí vận hành DN → miễn
    # DV tháng này chưa có doanh thu → so doanh thu tháng trước (200 tr): 20+30 = 50 tr → biên 75% → ổn
    assert ks.danh_gia(None, "DV-COA-NT-1026-03", 30e6) is None
    k = ks.danh_gia(None, "DV-COA-NT-1026", 200e6)                                # 220 tr > 200 tr → lỗ
    assert k["muc"] == "LO" and k["tham_chieu"] == "DV-COA-NT-0926" and "tháng trước" in k["ly_do"]
    k = ks.danh_gia(None, "TM-SIC-1026-01", 10e6)                                 # 90/100 → biên 10% < 15%
    assert k["muc"] == "BIEN_THAP" and k["bien"] == 10.0
    assert ks.danh_gia(None, "TM-SIC-1026", 1e6) is None                          # 81/100 → biên 19% → ổn
    assert ks.danh_gia(None, "TM-HEI-0326", 1e6)["muc"] == "CHUA_DT"              # TM chưa có đơn bán / doanh thu


class _Nd:
    def __init__(self, ma):
        self.id = 1
        self.vai_tro = type("VT", (), {"ma": ma})()


class _Dm:
    def __init__(self, ma, tien):
        self.id, self.so, self.ma_ban, self.don_hang_id, self.tong_tien = 5, "PO-5", ma, None, tien
        self.trang_thai, self.vuot_du_toan = "CHO_DUYET", None


def test_cong_duyet_po(monkeypatch):
    from app.routers import ncc
    dm = _Dm("TM-SIC-1026-01", 10e6)

    class _Db:
        def get(self, model, i):
            return dm if i == 5 else None

    monkeypatch.setattr(ncc, "_ma_ban_hang_po", lambda db, d: d.ma_ban)
    monkeypatch.setattr(ncc, "kiem_han_muc", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("qua cong LN")))
    with pytest.raises(HTTPException) as e:
        ncc.duyet_don_mua(5, False, _Db(), nd=_Nd("ADMIN"))                       # Admin / người khác → 403
    assert e.value.status_code == 403 and "📉" in e.value.detail and "chỉ CEO" in e.value.detail
    with pytest.raises(HTTPException) as e:
        ncc.duyet_don_mua(5, False, _Db(), nd=_Nd("CEO"))                         # CEO chưa xác nhận → 409
    assert e.value.status_code == 409 and "biên lợi nhuận chỉ 10.0%" in e.value.detail
    with pytest.raises(RuntimeError, match="qua cong LN"):
        ncc.duyet_don_mua(5, True, _Db(), nd=_Nd("CEO"))                          # CEO xác nhận → qua cổng 📉
    dm.ma_ban, dm.tong_tien = "TM-SIC-1026", 1e6
    with pytest.raises(RuntimeError, match="qua cong LN"):
        ncc.duyet_don_mua(5, False, _Db(), nd=_Nd("NV_KD"))                       # không có cờ → không hỏi


def test_ban_tuan(monkeypatch):
    from app.routers import ncc
    rows = [
        {"ma_ban": "DV-D10-0826", "nhom": "DV-D10-0826", "doanh_thu": 61e6, "tong_chi_phi": 100e6},
        {"ma_ban": "DV-COA-NT-0726-01", "nhom": "DV-COA-NT-0726", "doanh_thu": 400e6, "tong_chi_phi": 0},
        {"ma_ban": "DV-COA-NT-0726-02", "nhom": "DV-COA-NT-0726", "doanh_thu": 207e6, "tong_chi_phi": 721e6 - 400e6},
        {"ma_ban": "TM-HEI-0326", "nhom": "TM-HEI-0326", "doanh_thu": 0, "tong_chi_phi": 136e6, "chua_co_don_ban": True},
        {"ma_ban": "DV-COA-RO-1026", "nhom": "DV-COA-RO-1026", "doanh_thu": 0, "tong_chi_phi": 51e6},   # tháng hiện tại
        {"ma_ban": "OP-SV-0926", "nhom": "OP-SV-0926", "doanh_thu": 0, "tong_chi_phi": 165e6},          # OP → miễn
        {"ma_ban": "TM-SIC-0726-UP", "nhom": "TM-SIC-0726", "doanh_thu": 100e6, "tong_chi_phi": 96e6},
    ]
    monkeypatch.setattr(ncc, "chi_phi_theo_don", lambda db, _: rows)
    bc = ks.bao_cao_tuan(None, date(2026, 10, 27))
    assert [o["nhom"] for o in bc["lo"]] == ["DV-D10-0826"]                       # nhóm 0726 gộp lại thì lãi
    assert [o["nhom"] for o in bc["chua_dt"]] == ["TM-HEI-0326"]                  # bỏ tháng hiện tại + OP
    assert [o["nhom"] for o in bc["bien_thap"]] == ["TM-SIC-0726"]
    t = ks.noi_dung_tuan(bc)
    assert "DV-D10-0826" in t and "lỗ 39,0 tr" in t and "TM-HEI-0326" in t and "OP-SV" not in t
