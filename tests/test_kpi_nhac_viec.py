"""
⭐ KPI lời nhắc việc (mig 160, 29/10/2026): điểm thời gian tự động theo hạn, chấm kết quả 1–5 sao, quyền chấm,
mở lại việc thì bỏ điểm. SQLite trong bộ nhớ.
"""
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import kpi_nhac_viec as kp
from app import models as m
from app.routers import nhan_su as ns


def _r(**kw):
    base = dict(trang_thai="XONG", han_hoan_thanh=datetime(2026, 10, 29, 17, 0), thoi_diem=datetime(2026, 10, 29, 8, 0),
                xong_luc=None, ket_qua_diem=None)
    base.update(kw)
    return SimpleNamespace(**base)


NOW = datetime(2026, 10, 30, 9, 0)


def test_diem_thoi_gian_cac_muc():
    han = datetime(2026, 10, 29, 17, 0)
    assert kp.diem_thoi_gian(datetime(2026, 10, 29, 16, 30), han, NOW)[0:2] == (5, "đúng hạn")
    assert kp.diem_thoi_gian(datetime(2026, 10, 29, 10, 0), han, NOW)[0:2] == (5, "sớm 7 giờ")
    assert kp.diem_thoi_gian(datetime(2026, 10, 29, 19, 0), han, NOW)[0:2] == (4, "trễ 2 giờ")
    assert kp.diem_thoi_gian(datetime(2026, 10, 30, 10, 0), han, NOW)[0] == 3            # 17h
    assert kp.diem_thoi_gian(datetime(2026, 10, 31, 17, 0), han, NOW)[0] == 2            # 48h
    assert kp.diem_thoi_gian(datetime(2026, 11, 5, 17, 0), han, NOW)[0:2] == (1, "trễ 7 ngày")
    assert kp.diem_thoi_gian(None, han, NOW)[0:2] == (0, "đang trễ 16 giờ")             # chưa xong, quá hạn
    assert kp.diem_thoi_gian(None, datetime(2026, 11, 2, 9, 0), NOW)[0:2] == (None, "chưa đến hạn")


def test_tinh_kpi():
    k = kp.tinh_kpi(_r(xong_luc=datetime(2026, 10, 29, 16, 0), ket_qua_diem=4), NOW)
    assert k["tinh"] and k["tg_diem"] == 5 and k["kq_diem"] == 4 and k["kpi"] == 90 and not k["tam"] and k["kq_nhan"] == "Tốt"
    k = kp.tinh_kpi(_r(xong_luc=datetime(2026, 10, 29, 19, 0)), NOW)                   # trễ 2h, chưa chấm → tạm 80
    assert k["tg_diem"] == 4 and k["kpi"] == 80 and k["tam"]
    k = kp.tinh_kpi(_r(trang_thai="CHO_LAM"), NOW)                                       # chưa xong, quá hạn → 0 tạm
    assert k["tg_diem"] == 0 and k["kpi"] == 0 and k["tam"]
    k = kp.tinh_kpi(_r(trang_thai="CHO_LAM", han_hoan_thanh=datetime(2026, 11, 3, 9, 0)), NOW)
    assert k["tg_diem"] is None and k["kpi"] is None and k["tg_nhan"] == "chưa đến hạn"
    assert kp.tinh_kpi(_r(trang_thai="HUY"), NOW)["tinh"] is False
    k = kp.tinh_kpi(_r(han_hoan_thanh=None, xong_luc=datetime(2026, 10, 29, 8, 30)), NOW)   # không hạn → theo thời điểm nhắc
    assert k["tg_diem"] == 4
    k = kp.tinh_kpi(_r(xong_luc=None, ket_qua_diem=3), NOW)                              # xong không ghi giờ → chỉ kết quả
    assert k["tg_diem"] is None and k["kpi"] == 60


def test_duoc_cham():
    r = SimpleNamespace(nguoi_tao=1, nhan_vien_id=2)
    assert kp.duoc_cham(r, 1, False) and not kp.duoc_cham(r, 2, False) and kp.duoc_cham(r, 9, True)
    assert not kp.duoc_cham(SimpleNamespace(nguoi_tao=1, nhan_vien_id=1), 1, False)     # tự nhắc mình → không tự chấm


# ---------- route chấm ----------
@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setattr(ns, "ghi_audit", lambda *a, **k: None)
    eng = create_engine("sqlite://")
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien, m.NhacViec):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    s.add(m.VaiTro(ma="NV_DA", ten="NV")); s.add(m.VaiTro(ma="CEO", ten="Giám đốc")); s.flush()
    for i, em in enumerate(("an@x.vn", "binh@x.vn", "ceo@x.vn"), 1):
        s.add(m.NguoiDung(email=em, mat_khau_hash="x", vai_tro_id=2 if i == 3 else 1, trang_thai="HOAT_DONG"))
    s.flush()
    s.add(m.NhanVien(ma="NV01", ho_ten="An", trang_thai="DANG_LAM", nguoi_dung_id=1))
    s.add(m.NhanVien(ma="NV02", ho_ten="Bình", trang_thai="DANG_LAM", nguoi_dung_id=2))
    s.add(m.NhanVien(ma="NV03", ho_ten="Sếp", trang_thai="DANG_LAM", nguoi_dung_id=3))
    s.add(m.NhacViec(nguoi_tao=1, nhan_vien_id=2, tieu_de="Gọi khách", thoi_diem=datetime(2026, 10, 29, 8, 0),
                     han_hoan_thanh=datetime(2026, 10, 29, 17, 0), trang_thai="XONG", xong_luc=datetime(2026, 10, 29, 16, 0)))
    s.add(m.NhacViec(nguoi_tao=1, nhan_vien_id=2, tieu_de="Chưa xong", thoi_diem=datetime(2026, 10, 29, 8, 0),
                     han_hoan_thanh=datetime(2026, 10, 29, 17, 0), trang_thai="DANG_LAM"))
    s.commit()
    return s


def _nd(db, uid):
    u = db.get(m.NguoiDung, uid)
    u.vai_tro = db.get(m.VaiTro, u.vai_tro_id)
    return u


def test_cham_ket_qua_quyen_va_kpi(db):
    an, binh, ceo = _nd(db, 1), _nd(db, 2), _nd(db, 3)
    kq = ns.danh_gia_nhac_viec(1, ns.NhacViecDanhGiaVao(diem=4, ghi_chu="ổn"), db, an)     # người nhắc chấm
    assert kq["ok"] and kq["kpi"]["kpi"] == 90 and kq["kpi"]["kq_diem"] == 4
    r = db.get(m.NhacViec, 1)
    assert r.ket_qua_diem == 4 and r.ket_qua_ghi_chu == "ổn" and r.danh_gia_boi == 1 and r.danh_gia_luc is not None
    with pytest.raises(HTTPException) as e:                                              # người làm không tự chấm
        ns.danh_gia_nhac_viec(1, ns.NhacViecDanhGiaVao(diem=5), db, binh)
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:                                              # chưa xong không chấm
        ns.danh_gia_nhac_viec(2, ns.NhacViecDanhGiaVao(diem=3), db, ceo)
    assert e.value.status_code == 400
    with pytest.raises(HTTPException) as e:                                              # ngoài 1–5
        ns.danh_gia_nhac_viec(1, ns.NhacViecDanhGiaVao(diem=7), db, ceo)
    assert e.value.status_code == 400
    kq = ns.danh_gia_nhac_viec(1, ns.NhacViecDanhGiaVao(diem=2), db, ceo)                 # CEO chấm đè
    assert kq["kpi"]["kpi"] == 70
    # _nv_ra kèm kpi + tên người chấm
    ra = ns._nv_ra(db.get(m.NhacViec, 1), {1: "An", 2: "Bình", 3: "Sếp"})
    assert ra["ket_qua_diem"] == 2 and ra["danh_gia_ten"] == "Sếp" and ra["kpi"]["kpi"] == 70
    # mở lại việc → bỏ điểm kết quả
    ns.doi_trang_thai_nhac_viec(1, "CHO_LAM", db, ceo)
    r = db.get(m.NhacViec, 1)
    assert r.ket_qua_diem is None and r.xong_luc is None
