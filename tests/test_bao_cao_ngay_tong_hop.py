"""
Báo cáo ngày (mig 154): quy tắc ngày PHẢI báo cáo, tỉ lệ hoàn thành, danh sách thiếu để nhắc, giao việc.
Không cần PostgreSQL (SQLite trong bộ nhớ).
"""
from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import bao_cao_ngay_service as bs
from app import models as m
from app.routers import nhan_su as ns


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setattr(ns, "ghi_audit", lambda *a, **k: None)
    eng = create_engine("sqlite://")
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien, m.GiaoViec, m.BaoCaoNgay, m.NgayNghiOt, m.BaoCaoNhac):
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
    s.add(m.NguoiDung(email="a@x.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="HOAT_DONG"))
    s.add(m.NguoiDung(email="b@x.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="HOAT_DONG"))
    s.flush()
    s.add(m.NhanVien(ma="NV01", ho_ten="An", trang_thai="DANG_LAM", nguoi_dung_id=1))
    s.add(m.NhanVien(ma="NV02", ho_ten="Bình", trang_thai="DANG_LAM", nguoi_dung_id=2))
    s.add(m.NhanVien(ma="NV03", ho_ten="Chưa có TK", trang_thai="DANG_LAM"))
    s.commit()
    return s


def _bc(db, nv, d, ket_qua="xong", **kw):
    db.add(m.BaoCaoNgay(nhan_vien_id=nv, ngay=d, da_lam="làm", ket_qua=ket_qua, **kw)); db.commit()


def _wt(db, nv, d, loai, so_ngay=1, tt="DA_DUYET"):
    db.add(m.NgayNghiOt(nhan_vien_id=nv, ngay=d, loai=loai, so_gio=2 if loai.startswith("OT") else 0,
                        so_ngay=so_ngay, trang_thai=tt)); db.commit()


# Tuần 19–25/10/2026: T2 19 … T7 24, CN 25. 30/4 là lễ cố định.
def test_quy_tac_phai_bao_cao():
    assert bs.phai_bao_cao(date(2026, 10, 19), False, None) == (True, None)        # thứ Hai
    assert bs.phai_bao_cao(date(2026, 10, 24), False, None) == (True, None)        # thứ Bảy vẫn phải
    assert bs.phai_bao_cao(date(2026, 10, 25), False, None) == (False, "Chủ nhật")
    assert bs.phai_bao_cao(date(2026, 10, 25), True, None) == (True, None)         # CN có tăng ca → phải
    assert bs.phai_bao_cao(date(2026, 4, 30), False, None) == (False, "Ngày lễ")
    assert bs.phai_bao_cao(date(2026, 4, 30), True, None) == (True, None)          # lễ có tăng ca → phải
    assert bs.phai_bao_cao(date(2026, 10, 20), False, "NGHI_PHEP") == (False, "Nghỉ phép")
    assert bs.phai_bao_cao(date(2026, 10, 20), True, "NGHI_PHEP") == (True, None)  # có OT thì vẫn phải


def test_tong_hop_va_ty_le(db):
    hom_nay = date(2026, 10, 26)                         # thứ Hai
    _bc(db, 1, date(2026, 10, 19)); _bc(db, 1, date(2026, 10, 20)); _bc(db, 1, date(2026, 10, 22))
    _wt(db, 1, date(2026, 10, 21), "NGHI_PHEP")          # nghỉ phép → miễn
    _wt(db, 1, date(2026, 10, 25), "OT_CUOI_TUAN")       # CN tăng ca → phải, mà chưa báo cáo → thiếu
    _wt(db, 1, date(2026, 10, 23), "VIEC_RIENG_CO_LUONG", so_ngay=0.5)   # nửa ngày → vẫn phải → thiếu
    bc, ot, nghi = bs.nap_du_lieu(db, [1], date(2026, 10, 19), date(2026, 10, 31))
    th = bs.tong_hop_nv(db.get(m.NhanVien, 1), bc, ot, nghi, date(2026, 10, 19), date(2026, 10, 31), hom_nay)
    tt = {x["ngay"]: x["trang_thai"] for x in th["ngay"]}
    assert tt["2026-10-19"] == "DA" and tt["2026-10-21"] == "MIEN" and tt["2026-10-23"] == "THIEU"
    assert tt["2026-10-24"] == "THIEU" and tt["2026-10-25"] == "THIEU" and tt["2026-10-26"] == "CHO"
    assert [x["ly_do"] for x in th["ngay"] if x["ngay"] == "2026-10-21"] == ["Nghỉ phép"]
    # phải: 19,20,22,23,24,25 = 6 (21 miễn, 26 hôm nay chưa tới hạn); xong 3 → 50%
    assert (th["can"], th["xong"], th["thieu"], th["ty_le"]) == (6, 3, 3, 50.0)
    assert len(th["ngay"]) == 8                           # chỉ tới hôm nay, không liệt kê ngày tương lai


def test_ot_bi_tu_choi_khong_tinh_va_ngay_vao_lam(db):
    nv = db.get(m.NhanVien, 1); nv.ngay_vao_lam = date(2026, 10, 22); db.commit()
    _wt(db, 1, date(2026, 10, 25), "OT_CUOI_TUAN", tt="TU_CHOI")
    bc, ot, nghi = bs.nap_du_lieu(db, [1], date(2026, 10, 1), date(2026, 10, 31))
    th = bs.tong_hop_nv(nv, bc, ot, nghi, date(2026, 10, 1), date(2026, 10, 31), date(2026, 10, 26))
    assert th["ngay"][0]["ngay"] == "2026-10-22"          # trước ngày vào làm không tính
    assert {x["ngay"]: x["trang_thai"] for x in th["ngay"]}["2026-10-25"] == "MIEN"


def test_ds_thieu_de_nhac_bo_qua_nguoi_khong_tai_khoan_va_chu_nhat(db):
    _bc(db, 1, date(2026, 10, 23))
    assert [x["ten"] for x in bs.ds_thieu_bao_cao(db, date(2026, 10, 23))] == ["Bình"]   # NV03 không TK → bỏ
    assert bs.ds_thieu_bao_cao(db, date(2026, 10, 25)) == []                              # Chủ nhật
    _wt(db, 2, date(2026, 10, 25), "OT_CUOI_TUAN")
    assert [x["email"] for x in bs.ds_thieu_bao_cao(db, date(2026, 10, 25))] == ["b@x.vn"]
    assert bs.thieu_gan_day(db, 2, date(2026, 10, 26), 7) == [
        "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-24", "2026-10-25"]


def test_gui_nhac_moi_nguoi_mot_lan(db, monkeypatch):
    gui = []

    class Prov:
        che_do = "APP"

        def gui_ca_nhan(self, email, nd):
            gui.append((email, nd)); return {"da_gui": True}

    import app.chat_gateway as cg
    monkeypatch.setattr(cg, "dang_bat", lambda: True)
    monkeypatch.setattr(cg, "lay_chat_provider", lambda: Prov())
    kq = bs.gui_nhac(db, date(2026, 10, 23))
    assert kq["da_gui"] == 2 and sorted(e for e, _ in gui) == ["a@x.vn", "b@x.vn"]
    assert "Bạn chưa hoàn thành báo cáo ngày: 23/10/2026" in gui[0][1]
    kq2 = bs.gui_nhac(db, date(2026, 10, 23))             # lần 2: đã nhắc rồi → không gửi lại
    assert kq2["da_gui"] == 0 and kq2["da_nhac_truoc"] == 2 and len(gui) == 2


def test_gui_nhac_webhook_mot_tin_gop(db, monkeypatch):
    gui = []

    class Prov:
        che_do = "WEBHOOK"

        def gui_phong(self, nd):
            gui.append(nd); return {"da_gui": True}

    import app.chat_gateway as cg
    monkeypatch.setattr(cg, "dang_bat", lambda: True)
    monkeypatch.setattr(cg, "lay_chat_provider", lambda: Prov())
    kq = bs.gui_nhac(db, date(2026, 10, 23))
    assert kq["da_gui"] == 2 and kq["kieu"] == "PHONG_CHUNG" and len(gui) == 1
    assert "• An" in gui[0] and "• Bình" in gui[0] and "23/10/2026" in gui[0]


def _ceo(db):
    u = m.NguoiDung(email="ceo@x.vn", mat_khau_hash="x", vai_tro_id=2, trang_thai="HOAT_DONG")
    db.add(u); db.flush()
    db.add(m.NhanVien(ma="SV01", ho_ten="Giám đốc", trang_thai="DANG_LAM", nguoi_dung_id=u.id)); db.commit()
    return u


def test_chi_ceo_nhap_tay_4_truong(db):
    from fastapi import HTTPException
    nv_u = db.get(m.NguoiDung, 1)
    with pytest.raises(HTTPException) as e:          # nhân viên tự gõ người nhận / tên việc → bị chặn
        ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(ngay="2026-10-23", da_lam="x", ten_cong_viec="Tự đặt"), db, nd=nv_u)
    assert e.value.status_code == 403
    ok = ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(ngay="2026-10-23", da_lam="x"), db, nd=nv_u)   # không gõ thì vẫn gửi được
    with pytest.raises(HTTPException) as e:
        ns.sua_bao_cao_ngay(ok["id"], ns.BcNgaySuaVao(cv_ket_thuc="2026-10-30"), db, nd=nv_u)
    assert e.value.status_code == 403
    ceo = _ceo(db)
    ns.sua_bao_cao_ngay(ok["id"], ns.BcNgaySuaVao(giao_viec_email="A@x.vn", ten_cong_viec="Lắp bơm",
                                                  cv_bat_dau="2026-10-23", cv_ket_thuc="2026-10-25"), db, nd=ceo)
    r = db.get(m.BaoCaoNgay, ok["id"])
    assert (r.giao_viec_email, r.ten_cong_viec, r.cv_ket_thuc) == ("a@x.vn", "Lắp bơm", date(2026, 10, 25))
    ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(ngay="2026-10-23", da_lam="sửa lại"), db, nd=nv_u)   # NV gửi lại: giữ thông tin CEO nhập
    assert db.get(m.BaoCaoNgay, ok["id"]).ten_cong_viec == "Lắp bơm"


def test_ceo_giao_viec_nhan_vien_chon_khi_bao_cao(db):
    from fastapi import HTTPException
    ceo, an, binh = _ceo(db), db.get(m.NguoiDung, 1), db.get(m.NguoiDung, 2)
    g = ns.tao_giao_viec(ns.GiaoViecVao(email="A@X.vn", ten_cong_viec="Lắp bơm", bat_dau="2026-10-20", ket_thuc="2026-10-25"), db, nd=ceo)
    assert g["nhan_vien_id"] == 1 and g["ho_ten"] == "An"
    with pytest.raises(HTTPException):               # email không phải nhân viên đang làm
        ns.tao_giao_viec(ns.GiaoViecVao(email="ai@x.vn", ten_cong_viec="x"), db, nd=ceo)
    with pytest.raises(HTTPException):               # kết thúc trước bắt đầu
        ns.tao_giao_viec(ns.GiaoViecVao(email="a@x.vn", ten_cong_viec="x", bat_dau="2026-10-25", ket_thuc="2026-10-20"), db, nd=ceo)
    assert [x["id"] for x in ns.ds_giao_viec(None, db, nd=an)] == [g["id"]]       # An thấy việc của mình
    assert ns.ds_giao_viec(None, db, nd=binh) == []                               # Bình không thấy việc của An
    assert ns.ds_giao_viec("2026-10-26", db, nd=an) == []                         # hết hạn thì không còn hiệu lực
    ok = ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(ngay="2026-10-23", da_lam="lắp", giao_viec_id=g["id"]), db, nd=an)
    r = db.get(m.BaoCaoNgay, ok["id"])
    assert (r.giao_viec_id, r.ten_cong_viec, r.giao_viec_email, r.cv_bat_dau) == (g["id"], "Lắp bơm", "a@x.vn", date(2026, 10, 20))
    with pytest.raises(HTTPException):               # Bình không gắn được việc của An
        ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(ngay="2026-10-23", da_lam="x", giao_viec_id=g["id"]), db, nd=binh)
    ns.sua_giao_viec(g["id"], ns.GiaoViecVao(email="a@x.vn", ten_cong_viec="Lắp bơm + chạy thử", bat_dau="2026-10-20", ket_thuc="2026-10-27"), db, nd=ceo)
    assert db.get(m.BaoCaoNgay, ok["id"]).ten_cong_viec == "Lắp bơm + chạy thử"   # báo cáo đã gắn cập nhật theo
    ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(ngay="2026-10-23", da_lam="lắp"), db, nd=an)  # bỏ chọn việc → xóa bản chụp
    r = db.get(m.BaoCaoNgay, ok["id"])
    assert r.giao_viec_id is None and r.ten_cong_viec is None
    ns.xoa_giao_viec(g["id"], db, nd=ceo)
    assert ns.ds_giao_viec(None, db, nd=ceo) == []


def test_admin_giao_viec_va_nhan_tin_nguoi_nhan(db, monkeypatch):
    gui = []

    class Prov:
        che_do = "APP"

        def gui_ca_nhan(self, email, nd):
            gui.append((email, nd)); return {"da_gui": True}

    import app.chat_gateway as cg
    monkeypatch.setattr(cg, "dang_bat", lambda: True)
    monkeypatch.setattr(cg, "lay_chat_provider", lambda: Prov())
    db.add(m.VaiTro(ma="ADMIN", ten="Quản trị")); db.flush()
    ad = m.NguoiDung(email="admin@x.vn", mat_khau_hash="x", vai_tro_id=3, trang_thai="HOAT_DONG")
    db.add(ad); db.commit()
    assert ns._la_ceo(ad)                                   # Admin được giao việc / nhập 4 thông tin
    g = ns.tao_giao_viec(ns.GiaoViecVao(email="b@x.vn", ten_cong_viec="Chạy thử RO", bat_dau="2026-10-27",
                                        ket_thuc="2026-10-29"), db, nd=ad)
    assert g["thong_bao"]["da_gui"] and gui[-1][0] == "b@x.vn"
    assert "Bạn được giao việc: *Chạy thử RO*" in gui[-1][1] and "27/10/2026 → 29/10/2026" in gui[-1][1]
    assert "Người giao: admin@x.vn" in gui[-1][1]           # admin chưa có hồ sơ → hiện email
    n = len(gui)
    r = ns.sua_giao_viec(g["id"], ns.GiaoViecVao(email="b@x.vn", ten_cong_viec="Chạy thử RO", bat_dau="2026-10-27",
                                                 ket_thuc="2026-10-29"), db, nd=ad)
    assert "thong_bao" not in r and len(gui) == n           # không đổi gì → không nhắn
    ns.sua_giao_viec(g["id"], ns.GiaoViecVao(email="b@x.vn", ten_cong_viec="Chạy thử RO", bat_dau="2026-10-27",
                                             ket_thuc="2026-10-31"), db, nd=ad)
    assert "Cập nhật việc được giao cho bạn" in gui[-1][1] and "31/10/2026" in gui[-1][1]


def test_giao_viec_webhook_dang_phong_chung_ghi_ten(db, monkeypatch):
    gui = []

    class Prov:
        che_do = "WEBHOOK"

        def gui_phong(self, nd):
            gui.append(nd); return {"da_gui": True}

    import app.chat_gateway as cg
    monkeypatch.setattr(cg, "dang_bat", lambda: True)
    monkeypatch.setattr(cg, "lay_chat_provider", lambda: Prov())
    g = ns.tao_giao_viec(ns.GiaoViecVao(email="a@x.vn", ten_cong_viec="Lắp bơm"), db, nd=_ceo(db))
    assert g["thong_bao"]["kieu"] == "PHONG_CHUNG" and "Giao việc cho An: *Lắp bơm*" in gui[0]
