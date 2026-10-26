"""
Hồ sơ lương hiện «tai_khoan» (email tài khoản đã gắn) và PUT gan-tai-khoan gắn tài khoản CÓ SẴN vào hồ sơ
(nhân viên đăng nhập mới đăng ký tăng ca / nghỉ phép được ở Working time). Không cần PostgreSQL.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.deps import nhan_vien_id_cua
from app.routers import nhan_su as ns


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

    s.add(m.VaiTro(ma="NV_DA", ten="NV Dự án"))
    s.flush()
    s.add(m.NguoiDung(email="tuan@x.vn", mat_khau_hash="x", vai_tro_id=1))
    s.add(m.NhanVien(ma="NV07", ho_ten="Trần Anh Tuấn", trang_thai="DANG_LAM"))
    s.add(m.NhanVien(ma="NV08", ho_ten="Người khác", trang_thai="DANG_LAM"))
    s.commit()
    return s


def _gan(db, nv_id, email):
    return ns.gan_tai_khoan(nv_id, ns.GanTaiKhoanVao(email=email), db, nd=type("N", (), {"id": 1})())


def test_chua_gan_thi_khong_tim_thay_ho_so_va_tai_khoan_none(db):
    assert nhan_vien_id_cua(db, 1) is None                      # lý do Working time báo «chưa gắn hồ sơ»
    assert [h["tai_khoan"] for h in ns.ds_ho_so(db, None)] == [None, None]


def test_gan_tai_khoan_co_san_vao_ho_so(db):
    r = _gan(db, 1, "Tuan@X.vn")                                # không phân biệt hoa/thường
    assert r["ok"] and r["nhan_vien"] == "Trần Anh Tuấn"
    assert nhan_vien_id_cua(db, 1) == 1                         # giờ đăng ký tăng ca được
    ds = ns.ds_ho_so(db, None)
    assert ds[0]["tai_khoan"] == "tuan@x.vn" and ds[1]["tai_khoan"] is None


def test_gan_lai_sang_ho_so_khac_thi_go_lien_ket_cu(db):
    _gan(db, 1, "tuan@x.vn")
    _gan(db, 2, "tuan@x.vn")                                    # mỗi tài khoản chỉ 1 hồ sơ
    assert nhan_vien_id_cua(db, 1) == 2
    assert [h["tai_khoan"] for h in ns.ds_ho_so(db, None)] == [None, "tuan@x.vn"]


def test_email_khong_co_tai_khoan_thi_bao_loi(db):
    with pytest.raises(HTTPException) as e:
        _gan(db, 1, "khong-co@x.vn")
    assert e.value.status_code == 404
