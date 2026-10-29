"""
🕒 mig 161 (29/10/2026): du_toan_ban.tao_luc / cap_nhat_luc — mọi thay đổi dòng hoặc tiêu đề dự toán đều cập nhật giờ sửa gần nhất
(SQLAlchemy before_flush trong app/models.py); danh sách dự toán xếp dự toán vừa làm lên trên. SQLite trong bộ nhớ.
"""
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.routers import ncc

T = [datetime(2026, 10, 29, 8, 0), datetime(2026, 10, 29, 9, 0), datetime(2026, 10, 29, 10, 0),
     datetime(2026, 10, 29, 11, 0), datetime(2026, 10, 29, 12, 0)]


@pytest.fixture()
def db(monkeypatch):
    eng = create_engine("sqlite://")
    for t in (m.DuToanBan, m.DuToanBanMuc):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    gio = {"i": 0}
    monkeypatch.setattr(m, "_gio_vn", lambda: T[gio["i"]])
    s._gio = gio
    return s


def test_cap_nhat_luc_theo_moi_thay_doi(db):
    d = m.DuToanBan(ma="DT-1", ngay=date(2026, 10, 29)); db.add(d); db.commit()
    assert d.tao_luc == T[0] and d.cap_nhat_luc == T[0]                       # tạo → cả hai = giờ tạo
    db._gio["i"] = 1
    db.add(m.DuToanBanMuc(du_toan_id=d.id, ten="Bơm", so_luong=1, don_gia=1000)); db.commit()
    assert d.cap_nhat_luc == T[1]                                              # thêm dòng
    db._gio["i"] = 2
    muc = db.query(m.DuToanBanMuc).first(); muc.so_luong = 2; db.commit()
    assert d.cap_nhat_luc == T[2]                                              # sửa dòng
    db._gio["i"] = 3
    db.query(m.DuToanBan).all(); db.commit()                                   # chỉ đọc → không đổi
    assert d.cap_nhat_luc == T[2]
    d.mo_ta = "đổi mô tả"; db.commit()
    assert d.cap_nhat_luc == T[3]                                              # sửa tiêu đề
    db._gio["i"] = 4
    db.delete(muc); db.commit()
    assert d.cap_nhat_luc == T[4]                                              # xóa dòng
    assert d.tao_luc == T[0]                                                   # giờ tạo giữ nguyên
    # xóa cả dự toán lẫn dòng trong một lượt → không lỗi
    db.add(m.DuToanBanMuc(du_toan_id=d.id, ten="Ống", so_luong=1, don_gia=10)); db.commit()
    for x in db.query(m.DuToanBanMuc).all():
        db.delete(x)
    db.delete(d); db.commit()
    assert db.query(m.DuToanBan).count() == 0


def test_danh_sach_xep_vua_lam_len_tren(db):
    a = m.DuToanBan(ma="DT-A", ngay=date(2026, 10, 1)); db.add(a); db.commit()      # T0
    db._gio["i"] = 1
    b = m.DuToanBan(ma="DT-B", ngay=date(2026, 10, 2)); db.add(b); db.commit()      # T1
    ds = ncc.dtb_danh_sach(db, None)
    assert [x["ma"] for x in ds] == ["DT-B", "DT-A"]
    db._gio["i"] = 2
    db.add(m.DuToanBanMuc(du_toan_id=a.id, ten="Bơm", so_luong=1, don_gia=5000)); db.commit()   # A vừa sửa → lên đầu
    ds = ncc.dtb_danh_sach(db, None)
    assert [x["ma"] for x in ds] == ["DT-A", "DT-B"]
    assert ds[0]["cap_nhat_luc"] == "2026-10-29 10:00" and ds[0]["tao_luc"] == "2026-10-29 08:00" and ds[0]["tong"] == 5000
    # dữ liệu cũ chưa có giờ (NULL) → xuống cuối, không lỗi
    c = m.DuToanBan(ma="DT-C", ngay=date(2026, 9, 1)); db.add(c); db.commit()
    from sqlalchemy import update
    db.execute(update(m.DuToanBan).where(m.DuToanBan.id == c.id).values(tao_luc=None, cap_nhat_luc=None)); db.commit()
    db.expire_all()                                                             # xóa giờ bằng SQL thẳng (qua ORM thì máy lại ghi giờ)
    assert [x["ma"] for x in ncc.dtb_danh_sach(db, None)][-1] == "DT-C"
