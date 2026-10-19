"""
Test «Ngày bắt đầu thử việc» ở Hồ sơ lương (mig 151): lưu, giữ nguyên khi không gửi, xóa khi gửi null, trả ra ở danh sách hồ sơ.
Không cần PostgreSQL (SQLite trong bộ nhớ).
"""
from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.routers import nhan_su as ns
from app.schemas import HoSoLuongVao


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setattr(ns, "ghi_audit", lambda *a, **k: None)
    eng = create_engine("sqlite://")
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    s.add(m.NhanVien(ma="NV01", ho_ten="Nguyễn Văn A", loai_hop_dong="THU_VIEC", trang_thai="DANG_LAM"))
    s.commit()
    return s


def _sua(db, **kw):
    return ns.cap_nhat_ho_so(1, HoSoLuongVao(**kw), db, nd=type("N", (), {"id": 1})())


def test_luu_giu_nguyen_va_xoa_ngay_thu_viec(db):
    nv = db.get(m.NhanVien, 1)
    assert nv.ngay_bat_dau_thu_viec is None
    _sua(db, ngay_bat_dau_thu_viec="2026-09-15", luong_co_ban=10_000_000)
    assert db.get(m.NhanVien, 1).ngay_bat_dau_thu_viec == date(2026, 9, 15)
    hs = ns.ds_ho_so(db, None)[0]
    assert hs["ngay_bat_dau_thu_viec"] == "2026-09-15" and hs["loai_hop_dong"] == "THU_VIEC"
    _sua(db, luong_co_ban=12_000_000)                                  # không gửi trường → giữ nguyên
    assert db.get(m.NhanVien, 1).ngay_bat_dau_thu_viec == date(2026, 9, 15)
    _sua(db, ngay_bat_dau_thu_viec=None)                               # gửi null → xóa
    assert db.get(m.NhanVien, 1).ngay_bat_dau_thu_viec is None
    assert ns.ds_ho_so(db, None)[0]["ngay_bat_dau_thu_viec"] is None
