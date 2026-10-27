"""
🔒 Dòng dự toán ĐÃ MUA (27/10/2026): tạo PO từ dòng HOẶC PO lập tay cùng mã có đúng mặt hàng
→ người thường không sửa / xóa được (403); CEO / ADMIN phải xác nhận (409 → ?xac_nhan_khoa=1) và có ghi audit.
Kiểm hàm khóa dùng chung + lời gọi thật của dự toán hàng bán (SQLite, các bảng tối giản).
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.routers import ncc


class _Nd:
    def __init__(self, ma, id_=1):
        self.id = id_
        self.vai_tro = type("VT", (), {"ma": ma})()
        self.vai_tro_id = 1


def test_kiem_khoa_sua_phan_quyen():
    k = {"so_po": "PO-1", "kieu": "PO_TAY", "trang_thai": "DA_DUYET"}
    ncc.kiem_khoa_sua(None, "Ống", _Nd("NV_KD"), False)                 # chưa mua → ai cũng sửa
    with pytest.raises(HTTPException) as e:
        ncc.kiem_khoa_sua(k, "Ống", _Nd("NV_KD"), True)                  # người thường: xác nhận cũng không được
    assert e.value.status_code == 403 and "PO lập tay" in e.value.detail
    for vt in ("CEO", "ADMIN"):
        with pytest.raises(HTTPException) as e:
            ncc.kiem_khoa_sua(k, "Ống", _Nd(vt), False)                  # CEO / ADMIN chưa xác nhận → 409
        assert e.value.status_code == 409 and "🔒" in e.value.detail
        ncc.kiem_khoa_sua(k, "Ống", _Nd(vt), True)                       # đã xác nhận → cho qua


@pytest.fixture()
def db(monkeypatch):
    audit = []
    monkeypatch.setattr(ncc, "ghi_audit", lambda *a, **k: audit.append((a, k)))
    eng = create_engine("sqlite://")
    for t in (m.DonHang, m.DonMua, m.DonMuaCt):
        t.__table__.create(eng)
    with eng.begin() as c:
        # PO-7 lập TAY dưới mã DA-X-1026 có Ống PVC (hh 1); PO-8 TỪ CHỐI có Van bi (hh 2); PO-9 tạo từ dòng Bơm (hh 3)
        _c = "tien_hang, tien_thue, tong_tien, trang_thai_nhan, da_dat_hang, cho_lenh_bank, lenh_bank_tien, dinh_ky, de_nghi_tt, tt_du"
        _v = "0,0,0,'CHUA',0,0,0,0,0,0"
        c.exec_driver_sql(f"INSERT INTO don_mua (id, so, nha_cung_cap_id, ma_ban, trang_thai, ngay, {_c}) VALUES"
                          f" (7,'PO-7',1,'DA-X-1026','DA_DUYET','2026-10-20',{_v}), (8,'PO-8',1,'DA-X-1026','TU_CHOI','2026-10-21',{_v}),"
                          f" (9,'PO-9',1,'DA-X-1026','CHO_DUYET','2026-10-22',{_v})")
        c.exec_driver_sql("INSERT INTO don_mua_ct (id, don_mua_id, hang_hoa_id, so_luong, don_gia, thue_suat, so_luong_nhan) VALUES"
                          " (1,7,1,10,50000,8,0),(2,8,2,5,90000,8,0),(3,9,3,1,9000000,8,0)")
    s = sessionmaker(eng)()
    s._audit = audit
    return s


class _Dt:
    ma = "DA-X-1026"


class _Muc:
    def __init__(self, id_, ten, hh, po=None):
        self.id, self.ten, self.hang_hoa_id, self.don_mua_id = id_, ten, hh, po


def test_khoa_map_tao_po_va_po_lap_tay(db, monkeypatch):
    ds = [_Muc(1, "Ống PVC 60", 1), _Muc(2, "Van bi 60", 2), _Muc(3, "Bơm 5HP", 3, po=9), _Muc(4, "Ống PVC 60", None)]

    def po_hl(x):
        if not x.don_mua_id:
            return None
        dm = db.get(m.DonMua, x.don_mua_id)
        return dm if dm is not None and dm.trang_thai != "TU_CHOI" else None

    import app.gia_dau_vao as gdv
    monkeypatch.setattr(gdv, "hang_hoa_theo_ten", lambda _db, tens: {"ống pvc 60": 1})
    km = ncc.khoa_map_theo_ma(db, _Dt.ma, [(x.id, x.ten, x.hang_hoa_id, x) for x in ds], po_hl)
    assert km[1] == {"so_po": "PO-7", "kieu": "PO_TAY", "trang_thai": "DA_DUYET"}      # mua bằng PO lập tay
    assert km[2] is None                                                               # PO-8 bị từ chối → chưa mua
    assert km[3]["so_po"] == "PO-9" and km[3]["kieu"] == "TAO_PO"                     # tạo PO từ dòng
    assert km[4]["so_po"] == "PO-7"                                                    # chưa liên kết kho: khớp theo tên
    assert ncc.khoa_map_theo_ma(db, "MA-KHAC", [(1, "Ống PVC 60", 1, ds[0])], po_hl)[1] is None   # khác mã → không khóa
