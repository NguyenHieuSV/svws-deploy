"""
Bước 3 báo giá (28/10/2026): ⭐ tùy chọn ngoài tổng chính; phiên bản Rev.A/B lưu khi gửi khách; so sánh với lần gửi trước.
SQLite trong bộ nhớ, dự toán thay bằng dữ liệu giả.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import bao_gia_ks as bk
from app import models as m
from app.bao_gia_pdf import tinh_bao_gia, tinh_tuy_chon


@pytest.fixture()
def db(monkeypatch):
    eng = create_engine("sqlite://")
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien, m.BaoGiaForm, m.BaoGiaPhienBan):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    monkeypatch.setattr(bk, "tim_du_toan", lambda db_, bgf: {"loai": "DTB", "id": 1, "ma": "DA-X-1026", "so_dong": 2,
                                                             "dong_thieu_gia": [], "tong": 80e6, "so_bo": 0, "dong": [],
                                                             "ngoai_du_toan": [], "ngoai_chua_uoc": []})
    return s


def _nd(gia_bom, them_tuy_chon=True):
    its = [{"dt_muc_id": 1, "ten": "Bơm", "so_luong": 1, "don_gia": gia_bom, "gia_von": 60e6, "vat_pct": 8},
           {"dt_muc_id": 2, "ten": "Ống", "so_luong": 10, "don_gia": 2e6, "gia_von": 1e6, "vat_pct": 8}]
    if them_tuy_chon:
        its.append({"ten": "Bộ lọc dự phòng", "so_luong": 1, "don_gia": 15e6, "gia_von": 10e6, "tuy_chon": True, "vat_pct": 8})
    return {"so": "DA-X-1026", "items": its, "vat_pct": 8}


def test_tuy_chon_ngoai_tong_chinh():
    nd = _nd(100e6)
    assert tinh_bao_gia(nd)[0] == 120e6 and tinh_tuy_chon(nd) == 15e6        # 100 + 20, tùy chọn 15 để ngoài


def test_phien_ban_va_so_sanh(db):
    b = m.BaoGiaForm(so="DA-X-1026", noi_dung=_nd(100e6), trang_thai="DA_DUYET")
    db.add(b); db.commit()
    assert bk.so_sanh_lan_truoc(db, b) is None                               # chưa gửi lần nào
    r1 = bk.luu_phien_ban(db, b, 1, "kh@x.vn"); db.commit()
    assert r1["rev"] == "A" and r1["tong_chua_vat"] == 120e6
    ds = bk.ds_phien_ban(db, b.id)
    assert ds[0]["rev"] == "A" and ds[0]["tong_tuy_chon"] == 15e6 and ds[0]["gia_von"] == 80e6 and ds[0]["so_dong"] == 3
    assert ds[0]["bien"] == round((120e6 - 80e6) / 120e6 * 100, 1)
    # khách ép giá: hạ bơm 100 → 90, bớt dòng tùy chọn, thêm dòng vận chuyển
    nd2 = _nd(90e6, them_tuy_chon=False)
    nd2["items"].append({"ten": "Vận chuyển", "so_luong": 1, "don_gia": 3e6, "gia_von": 2e6, "ngoai_du_toan": True})
    b.noi_dung = nd2; db.commit()
    ss = bk.so_sanh_lan_truoc(db, b)
    assert ss["rev"] == "A" and ss["tong_truoc"] == 120e6 and ss["tong_nay"] == 113e6 and ss["chenh_tong"] == -7e6
    assert ss["them"] == ["Vận chuyển"] and ss["bot"] == ["Bộ lọc dự phòng"]
    assert ss["doi_gia"] == [{"ten": "Bơm", "cu": 100e6, "moi": 90e6}]
    r2 = bk.luu_phien_ban(db, b, 1, "kh@x.vn"); db.commit()
    assert r2["rev"] == "B" and len(bk.ds_phien_ban(db, b.id)) == 2
