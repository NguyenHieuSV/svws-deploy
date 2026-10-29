"""
% tiến độ công việc trong báo cáo ngày (mig 159, 29/10/2026): bắt buộc nhập, giao_viec nhớ % mới nhất, đạt 100% → mốc
hoàn thành + thông báo, chậm so với thời gian → cảnh báo lúc gửi + danh sách nhắc. SQLite trong bộ nhớ, không gửi chat thật.
"""
from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app import tien_do_service as ts
from app.routers import nhan_su as ns


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setattr(ns, "ghi_audit", lambda *a, **k: None)
    eng = create_engine("sqlite://")
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien, m.GiaoViec, m.BaoCaoNgay, m.TepDinhKem):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    s.add(m.VaiTro(ma="NV_DA", ten="NV Dự án")); s.add(m.VaiTro(ma="CEO", ten="Giám đốc")); s.flush()
    s.add(m.NguoiDung(email="an@x.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="HOAT_DONG"))
    s.add(m.NguoiDung(email="ceo@x.vn", mat_khau_hash="x", vai_tro_id=2, trang_thai="HOAT_DONG"))
    s.flush()
    s.add(m.NhanVien(ma="NV01", ho_ten="An", trang_thai="DANG_LAM", nguoi_dung_id=1))
    s.add(m.NhanVien(ma="NV02", ho_ten="Bình", trang_thai="DANG_LAM"))
    s.commit()
    return s


def _nd(db, uid):
    u = db.get(m.NguoiDung, uid)
    u.vai_tro = db.get(m.VaiTro, u.vai_tro_id)
    return u


def _giao(db, nv=1, bd=date(2026, 11, 2), kt=date(2026, 11, 11), nguoi_giao=2):
    g = m.GiaoViec(nhan_vien_id=nv, email="an@x.vn", ten_cong_viec="Lắp cụm RO", bat_dau=bd, ket_thuc=kt,
                   ma_du_an="DA-ABC-1126", nguoi_giao=nguoi_giao)
    db.add(g); db.commit()
    return g


def _vao(**kw):
    return ns.BaoCaoNgayVao(**dict({"da_lam": "làm việc", "ket_qua": "ok"}, **kw))


# ---------- công thức theo thời gian ----------
def test_tien_do_theo_thoi_gian():
    bd, kt = date(2026, 11, 2), date(2026, 11, 11)                       # 10 ngày
    assert ts.tien_do_theo_thoi_gian(bd, kt, date(2026, 11, 1)) == 0.0   # chưa bắt đầu
    assert ts.tien_do_theo_thoi_gian(bd, kt, bd) == 10.0                 # ngày đầu = 1/10
    assert ts.tien_do_theo_thoi_gian(bd, kt, date(2026, 11, 6)) == 50.0  # ngày 5/10
    assert ts.tien_do_theo_thoi_gian(bd, kt, kt) == 100.0                # ngày cuối
    assert ts.tien_do_theo_thoi_gian(bd, kt, date(2026, 11, 20)) == 100.0
    assert ts.tien_do_theo_thoi_gian(None, kt, bd) is None
    assert ts.ngay_thu(bd, kt, date(2026, 11, 6)) == (5, 10)


def test_danh_gia_cham_dung_qua_han(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "tien_do_lech_diem", 20)
    bd, kt = date(2026, 11, 2), date(2026, 11, 11)
    d = ts.danh_gia(20, bd, kt, date(2026, 11, 6))                        # theo TG 50, báo 20 → chậm 30
    assert d["ky_vong"] == 50.0 and d["cham"] and not d["qua_han"] and d["lech"] == -30.0 and "chậm 30" in d["nhan"]
    d = ts.danh_gia(40, bd, kt, date(2026, 11, 6))                        # chậm 10 < ngưỡng 20 → đúng tiến độ
    assert not d["cham"] and "đúng tiến độ" in d["nhan"]
    d = ts.danh_gia(100, bd, kt, date(2026, 11, 6))
    assert not d["cham"] and d["nhan"].startswith("✅")
    d = ts.danh_gia(80, bd, kt, date(2026, 11, 13))                       # quá hạn 2 ngày, chưa 100
    assert d["cham"] and d["qua_han"] and "quá hạn 2 ngày" in d["nhan"]
    d = ts.danh_gia(None, bd, kt, date(2026, 11, 2))                      # chưa báo, mới ngày 1/10 (10%) → chưa chậm
    assert not d["cham"]
    d = ts.danh_gia(None, bd, kt, date(2026, 11, 3))                      # chưa báo, ngày 2/10 (20%) = ngưỡng → chậm
    assert d["cham"] and "chưa báo" in d["nhan"]
    assert ts.danh_gia(30, None, None, date(2026, 11, 3))["ky_vong"] is None


# ---------- gửi báo cáo: bắt buộc % · giao_viec nhớ % mới nhất · 100% → hoàn thành ----------
def test_gui_bao_cao_bat_buoc_tien_do(db):
    nd = _nd(db, 1)
    with pytest.raises(HTTPException) as e:
        ns.gui_bao_cao_ngay(_vao(ngay="2026-11-03"), db, nd)
    assert e.value.status_code == 400 and "tiến độ" in e.value.detail
    with pytest.raises(HTTPException) as e:
        ns.gui_bao_cao_ngay(_vao(ngay="2026-11-03", tien_do=120), db, nd)
    assert e.value.status_code == 400


def test_giao_viec_nho_tien_do_moi_nhat_va_hoan_thanh(db, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "tien_do_lech_diem", 20)
    nd = _nd(db, 1)
    g = _giao(db)                                                          # 02 → 11/11 (10 ngày)
    kq = ns.gui_bao_cao_ngay(_vao(ngay="2026-11-03", tien_do=20, giao_viec_id=g.id), db, nd)   # ngày 2/10 → TG 20%
    assert kq["ok"] and kq["tien_do"] == 20 and kq["canh_bao_tien_do"] is None and not kq["hoan_thanh"]
    db.refresh(g)
    assert float(g.tien_do) == 20 and g.hoan_thanh_luc is None
    # ngày 6/10 (TG 60%) báo 25 → chậm 35 điểm → cảnh báo ngay
    kq = ns.gui_bao_cao_ngay(_vao(ngay="2026-11-07", tien_do=25, giao_viec_id=g.id), db, nd)
    assert kq["canh_bao_tien_do"] and "chậm 35" in kq["canh_bao_tien_do"]
    db.refresh(g); assert float(g.tien_do) == 25
    # sửa lại báo cáo CŨ (ngày 03) lên 90 → % mới nhất vẫn theo ngày gần nhất (25), không nhảy lên 90
    r3 = db.query(m.BaoCaoNgay).filter_by(ngay=date(2026, 11, 3)).first()
    ns.sua_bao_cao_ngay(r3.id, ns.BcNgaySuaVao(tien_do=90), db, nd)
    db.refresh(g); assert float(g.tien_do) == 25
    # ngày 10 báo 100 → hoàn thành lần đầu + có mục thông báo (chat DEMO → không gửi, có lý do)
    kq = ns.gui_bao_cao_ngay(_vao(ngay="2026-11-10", tien_do=100, giao_viec_id=g.id), db, nd)
    assert kq["hoan_thanh"] and kq["thong_bao"]["da_gui"] is False and kq["thong_bao"]["loi"]
    db.refresh(g); assert float(g.tien_do) == 100 and g.hoan_thanh_luc is not None
    # gửi lại cùng ngày vẫn 100 → không báo hoàn thành lần hai
    kq = ns.gui_bao_cao_ngay(_vao(ngay="2026-11-10", tien_do=100, giao_viec_id=g.id), db, nd)
    assert not kq["hoan_thanh"]
    # xóa báo cáo 100 → việc tụt về 25, bỏ mốc hoàn thành
    r10 = db.query(m.BaoCaoNgay).filter_by(ngay=date(2026, 11, 10)).first()
    ns.xoa_bao_cao_ngay(r10.id, db, nd)
    db.refresh(g); assert float(g.tien_do) == 25 and g.hoan_thanh_luc is None   # báo cáo ngày 07 (25) là gần nhất còn lại
    # _gv_ra có đánh giá
    ra = ns._gv_ra(g, db.get(m.NhanVien, 1))
    assert "tien_do" in ra and "danh_gia" in ra and ra["danh_gia"]["ky_vong"] is not None


def test_noi_dung_hoan_thanh_som_tre(db):
    g = _giao(db)
    nv = db.get(m.NhanVien, 1)
    s = ts.noi_dung_hoan_thanh(g, nv, date(2026, 11, 9), "Hiếu")
    assert "HOÀN THÀNH 100%" in s and "sớm 2 ngày" in s and "DA-ABC-1126" in s and "Hiếu" in s
    assert "trễ 3 ngày" in ts.noi_dung_hoan_thanh(g, nv, date(2026, 11, 14), "Hiếu")
    assert "đúng hạn" in ts.noi_dung_hoan_thanh(g, nv, date(2026, 11, 11), "Hiếu")


# ---------- danh sách + nhắc chậm tiến độ ----------
def test_ds_cham_va_nhac(db, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "tien_do_lech_diem", 20)
    g1 = _giao(db, nv=1, bd=date(2026, 11, 2), kt=date(2026, 11, 11))      # An: có tài khoản
    g2 = _giao(db, nv=2, bd=date(2026, 11, 2), kt=date(2026, 11, 11))      # Bình: không tài khoản
    g3 = _giao(db, nv=1, bd=date(2026, 10, 1), kt=date(2026, 10, 5))       # quá hạn > 14 ngày → thôi nhắc
    g4 = _giao(db, nv=1, bd=date(2026, 12, 1), kt=date(2026, 12, 9))       # chưa bắt đầu
    g1.tien_do = 10; g2.tien_do = None; g3.tien_do = 50; g4.tien_do = None; db.commit()
    hom_nay = date(2026, 11, 7)                                            # ngày 6/10 → TG 60%
    ds = ts.ds_cham_tien_do(db, hom_nay)
    ids = {x["giao_viec_id"] for x in ds}
    assert ids == {g1.id, g2.id}
    x1 = next(x for x in ds if x["giao_viec_id"] == g1.id)
    assert x1["ky_vong"] == 60.0 and x1["tien_do"] == 10 and x1["co_tai_khoan"] and not x1["da_nhac_hom_nay"]
    x2 = next(x for x in ds if x["giao_viec_id"] == g2.id)
    assert x2["tien_do"] is None and not x2["co_tai_khoan"]
    nd_ = ts.noi_dung_cham_chung(ds)
    assert "2 việc" in nd_ and "theo thời gian 60%" in nd_ and "chưa báo tiến độ" in nd_
    assert "Lắp cụm RO" in ts.noi_dung_cham_rieng(x1)
    # chat DEMO: không gửi, có lý do; không đánh dấu đã nhắc
    kq = ts.nhac_cham_tien_do(db, hom_nay)
    assert kq["cham"] == 2 and kq["da_gui"] == 0 and kq["khong_tai_khoan"] == 1 and kq["loi"]
    db.refresh(g1); assert g1.nhac_lech_ngay is None
    # giả lập chat WEBHOOK gửi được → đánh dấu đã nhắc hôm nay, lần hai không gửi lại
    prov = SimpleNamespace(che_do="WEBHOOK", gui_phong=lambda nd: {"da_gui": True})
    monkeypatch.setattr("app.chat_gateway.dang_bat", lambda: True)
    monkeypatch.setattr("app.chat_gateway.lay_chat_provider", lambda: prov)
    kq = ts.nhac_cham_tien_do(db, hom_nay)
    assert kq["da_gui"] == 1 and kq["kieu"] == "PHONG_CHUNG" and kq["ten"] == ["An"]
    db.refresh(g1); assert g1.nhac_lech_ngay == hom_nay
    kq = ts.nhac_cham_tien_do(db, hom_nay)
    assert kq["da_gui"] == 0 and kq["da_nhac_truoc"] == 1
    # đã 100% thì không còn trong danh sách
    g1.tien_do = 100; db.commit()
    assert all(x["giao_viec_id"] != g1.id for x in ts.ds_cham_tien_do(db, hom_nay))


def test_thong_bao_hoan_thanh_rieng_nguoi_giao(db, monkeypatch):
    g = _giao(db)
    nv = db.get(m.NhanVien, 1)
    gui = {}
    prov = SimpleNamespace(che_do="APP", gui_phong=lambda nd: {"da_gui": True},
                           gui_ca_nhan=lambda email, nd: gui.setdefault("den", email) and {"da_gui": True})
    monkeypatch.setattr("app.chat_gateway.dang_bat", lambda: True)
    monkeypatch.setattr("app.chat_gateway.lay_chat_provider", lambda: prov)
    kq = ts.thong_bao_hoan_thanh(db, g, nv, date(2026, 11, 9))
    assert kq["da_gui"] and kq["kieu"] == "RIENG" and gui["den"] == "ceo@x.vn"


def test_cap_nhat_giao_viec_khong_co_bao_cao(db):
    g = _giao(db)
    kq = ts.cap_nhat_giao_viec(db, g, datetime(2026, 11, 3, 9, 0))
    assert kq["tien_do"] is None and not kq["vua_100"] and g.tien_do is None
