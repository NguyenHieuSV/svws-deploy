"""
📋/📉 Kiểm soát báo giá ↔ dự toán (28/10/2026): bắt buộc có dự toán đủ dòng + giá; biên so với dự toán;
cổng trình duyệt / duyệt / gửi (người thường bị chặn, CEO phải xác nhận). Dự toán được thay bằng dữ liệu giả.
"""
import pytest
from fastapi import HTTPException

from app import bao_gia_ks as bk
from app.config import settings

_TIM_DU_TOAN_THAT = bk.tim_du_toan          # giữ hàm thật — fixture bên dưới thay bk.tim_du_toan bằng dữ liệu giả


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


def test_buoc2_khong_chao_ngoai_du_toan_doi_gia(monkeypatch):
    # dự toán giả có từng dòng
    DT2 = {"loai": "DTB", "id": 9, "ma": "DA-B2-1026", "so_dong": 2, "dong_thieu_gia": [], "tong": 100e6,
           "dong": [{"id": 1, "ten": "Bơm", "so_luong": 1, "don_gia": 60e6}, {"id": 2, "ten": "Ống", "so_luong": 10, "don_gia": 4e6}]}
    def _gia(db, bgf):
        its = (bgf.noi_dung or {}).get("items") or []
        ng = [it for it in its if it.get("ngoai_du_toan") and not it.get("khong_chao")]
        return dict(DT2, so_bo=sum(1 for it in its if it.get("khong_chao")),
                    ngoai_du_toan=[{"ten": it["ten"], "so_luong": it["so_luong"], "gia_von": it["gia_von"], "don_gia": it["don_gia"]} for it in ng],
                    ngoai_chua_uoc=[it["ten"] for it in ng if not it.get("gia_von")])
    monkeypatch.setattr(bk, "tim_du_toan", _gia)
    nd = {"so": "DA-B2-1026", "items": [
        {"dt_muc_id": 1, "ten": "Bơm", "so_luong": 1, "gia_von": 60e6, "don_gia": 80e6},
        {"dt_muc_id": 2, "ten": "Ống", "so_luong": 10, "gia_von": 5e6, "don_gia": 7e6, "khong_chao": True},   # giá vốn trong BG 5 ≠ 4 nhưng không chào → bỏ qua
        {"ngoai_du_toan": True, "ten": "Vận chuyển", "so_luong": 1, "gia_von": 0, "don_gia": 3e6},
    ]}
    doi = bk.dt_doi_gia(DT2, nd)
    assert doi == []                                                   # dòng không chào không báo đổi giá
    nd["items"][0]["gia_von"] = 55e6
    assert bk.dt_doi_gia(DT2, nd)[0]["moi"] == 60e6                    # dự toán đổi giá → báo
    k = bk.kiem_tra(None, _Bgf("DA-B2-1026", nd["items"]))
    assert k["tong_bg"] == 83e6                                        # bỏ dòng không chào (70 tr)
    assert k["ngoai_chua_uoc"] == ["Vận chuyển"]
    with pytest.raises(HTTPException) as e:                            # ngoài dự toán chưa ước → người thường bị chặn
        bk.cong(None, _Bgf("DA-B2-1026", nd["items"]), _Nd("NV_KD"), False, "trình duyệt")
    assert e.value.status_code == 400 and "chưa có chi phí dự kiến" in e.value.detail
    with pytest.raises(HTTPException) as e:
        bk.cong(None, _Bgf("DA-B2-1026", nd["items"]), _Nd("CEO"), False, "trình duyệt")
    assert e.value.status_code == 409
    assert bk.mau_dieu_khoan_theo_ma("DV-COA-NT-1026") == "DV" and bk.mau_dieu_khoan_theo_ma("SV-0726-16") == "TM"
    assert "commissioning" in bk.MAU_DIEU_KHOAN["DA"]["tt"]


def test_tim_du_toan_tru_khong_chao_cong_ngoai_du_toan(monkeypatch):
    import app.bao_gia_ks as m
    class _M:  # dòng dự toán
        def __init__(s, i, ten, sl, g): s.id, s.ten, s.so_luong, s.don_gia = i, ten, sl, g
    class _Q:
        def __init__(s, rows): s.rows = rows
        def filter_by(s, **k): return s
        def all(s): return s.rows
    class _Db:
        def get(s, model, i): return type("D", (), {"id": 9, "ma": "DA-B2-1026"})()
        def query(s, model):
            from app.models import DuToanBanMuc
            if model is DuToanBanMuc:
                return _Q([_M(1, "Bơm", 1, 60e6), _M(2, "Ống", 10, 4e6), _M(3, "Chưa giá", 2, 0)])
            return _Q([])
    bgf = _Bgf("DA-B2-1026", [
        {"dt_muc_id": 1, "ten": "Bơm", "so_luong": 1, "gia_von": 60e6, "don_gia": 80e6},
        {"dt_muc_id": 3, "ten": "Chưa giá", "so_luong": 2, "gia_von": 0, "don_gia": 1e6, "khong_chao": True},
        {"ngoai_du_toan": True, "ten": "Vận chuyển", "so_luong": 2, "gia_von": 1.5e6, "don_gia": 2e6},
    ], du_toan_id=9)
    dt = _TIM_DU_TOAN_THAT(_Db(), bgf)
    assert dt["tong"] == 60e6 + 40e6 + 3e6                              # bỏ dòng 3 (không chào), cộng ngoài DT 2×1,5
    assert dt["dong_thieu_gia"] == [] and dt["so_bo"] == 1              # dòng chưa giá bị bỏ → không còn thiếu giá
    assert dt["ngoai_du_toan"][0]["ten"] == "Vận chuyển" and dt["ngoai_chua_uoc"] == []
