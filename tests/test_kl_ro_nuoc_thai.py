"""
🚫 Quy tắc đồng hồ khối lượng (anh Hiếu 31/10/2026): dự án NƯỚC THẢI chỉ tính chỉ số nước thải, không nhận đồng hồ RO tính tiền
(nước RO thuộc dự án tái sử dụng cùng khách); chỉ số chỉ ghi được cho hệ thống có trong danh mục của dự án. SQLite trong bộ nhớ.
"""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.routers import cho_thue_ops as ct

NV = SimpleNamespace(id=1, vai_tro=SimpleNamespace(ma="CEO"))


@pytest.fixture()
def db(monkeypatch):
    eng = create_engine("sqlite://")
    for t in (m.TaiSanChoThue, m.CtBcvhChiTieu, m.CtBaoCaoVh):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    monkeypatch.setattr(ct, "ghi_audit", lambda *a, **k: None)
    monkeypatch.setattr(ct, "nhan_vien_id_cua", lambda db_, uid: 1)
    s.add(m.TaiSanChoThue(ma="DV-X-NT-2024", ten="Vận hành NT", loai_he_thong="NUOC_THAI", khach_hang_id=5))
    s.add(m.TaiSanChoThue(ma="DV-X-RO-2024", ten="Tái sử dụng RO", loai_he_thong="NUOC_TAI_SU_DUNG", khach_hang_id=5))
    s.commit()
    return s


def _ct(loai, ten, tinh_tien=True, dv="m3"):
    return ct.CtChiTieuVao(loai=loai, chi_tieu=ten, don_vi=dv, tinh_tien=tinh_tien)


def test_nuoc_thai_khong_nhan_dong_ho_ro(db):
    with pytest.raises(HTTPException) as e:                                   # RO tính tiền → chặn, chỉ sang dự án RO
        ct.them_chi_tieu(1, _ct("KHOI_LUONG", "Nước ro"), db, NV)
    assert e.value.status_code == 400 and "DV-X-RO-2024" in e.value.detail and "RO" in e.value.detail
    with pytest.raises(HTTPException):
        ct.them_chi_tieu(1, _ct("KHOI_LUONG", "RO line 1"), db, NV)
    ct.them_chi_tieu(1, _ct("KHOI_LUONG", "Nước RO vào DAF", tinh_tien=False), db, NV)   # RO tham khảo → được
    ct.them_chi_tieu(1, _ct("KHOI_LUONG", "Nước thải"), db, NV)
    ct.them_chi_tieu(1, _ct("KY_THUAT", "pH RO"), db, NV)                              # chỉ tiêu kỹ thuật không bị quy tắc
    ct.them_chi_tieu(2, _ct("KHOI_LUONG", "RO"), db, NV)                               # dự án RO nhận bình thường
    ten = [c.chi_tieu for c in db.query(m.CtBcvhChiTieu).filter_by(tai_san_id=1, loai="KHOI_LUONG").all()]
    assert ten == ["Nước RO vào DAF", "Nước thải"]
    # bật tính tiền cho đồng hồ RO tham khảo ở dự án nước thải → chặn
    c_daf = db.query(m.CtBcvhChiTieu).filter_by(chi_tieu="Nước RO vào DAF").one()
    with pytest.raises(HTTPException):
        ct.sua_chi_tieu(c_daf.id, ct.CtChiTieuSua(tinh_tien=True), db, NV)


def test_ghi_chi_so_phai_dung_danh_muc(db):
    ct.them_chi_tieu(1, _ct("KHOI_LUONG", "Nước thải"), db, NV)
    kq = ct.luu_bao_cao_kl(1, ct.BcKlBatch(ngay=date(2026, 10, 31), dong=[ct.BcKlDong(he_thong="Nước thải", chi_so=1000)]),
                           False, db, NV)
    assert kq["so_dong"] == 1
    with pytest.raises(HTTPException) as e:                                   # không có trong danh mục
        ct.luu_bao_cao_kl(1, ct.BcKlBatch(dong=[ct.BcKlDong(he_thong="Nước ro", chi_so=5)]), False, db, NV)
    assert e.value.status_code == 400 and "danh mục" in e.value.detail
    # dự án chưa có danh mục → không ràng buộc danh mục, nhưng nước thải vẫn không nhận RO
    db.add(m.TaiSanChoThue(ma="DV-Y-NT-2025", ten="NT2", loai_he_thong="NUOC_THAI")); db.commit()
    ct.luu_bao_cao_kl(3, ct.BcKlBatch(dong=[ct.BcKlDong(he_thong="Nước thải", chi_so=10)]), False, db, NV)
    with pytest.raises(HTTPException):
        ct.luu_bao_cao_kl(3, ct.BcKlBatch(dong=[ct.BcKlDong(he_thong="RO", chi_so=10)]), False, db, NV)


def test_chuyen_dong_ho_ro_vao_du_an_nuoc_thai_bi_chan(db):
    ct.them_chi_tieu(2, _ct("KHOI_LUONG", "RO"), db, NV)
    ct.luu_bao_cao_kl(2, ct.BcKlBatch(ngay=date(2026, 10, 30), dong=[ct.BcKlDong(he_thong="RO", chi_so=100)]), False, db, NV)
    with pytest.raises(HTTPException) as e:
        ct.chuyen_he_thong_kl(2, ct.ChuyenKlVao(he_thong="RO", tai_san_id_den=1), db, NV, None)
    assert e.value.status_code == 400 and "nước thải" in e.value.detail.lower()
    assert db.query(m.CtBaoCaoVh).filter_by(tai_san_id=2).count() == 1              # không bị chuyển
