"""
🔒 Khóa tài khoản khi không phản hồi việc được giao (mig 168, app/khoa_nhac_viec.py — anh Hiếu 05/11/2026).
SQLite trong bộ nhớ, Chat ở chế độ DEMO (không gửi thật), audit tắt.
"""
from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import khoa_nhac_viec as kn
from app import models as m
from app.config import settings

NOW = datetime(2026, 11, 7, 9, 0)            # sáng 07/11 — giờ quét


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setattr(kn, "ghi_audit", lambda *a, **k: None)
    monkeypatch.setattr(settings, "chat_provider", "DEMO")
    monkeypatch.setattr(settings, "nhac_viec_khoa_tu_dong", True)
    monkeypatch.setattr(settings, "nhac_viec_khoa_sau_ngay", 2)
    monkeypatch.setattr(settings, "nhac_viec_khoa_tu", "2026-11-05")
    eng = create_engine("sqlite://")
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien, m.NhacViec, m.NhacViecKhoa):
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
    s.add(m.NguoiDung(email="an@x.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="HOAT_DONG"))      # 1 An
    s.add(m.NguoiDung(email="ceo@x.vn", mat_khau_hash="x", vai_tro_id=2, trang_thai="HOAT_DONG"))     # 2 CEO
    s.add(m.NguoiDung(email="cu@x.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="KHOA"))           # 3 Cường (đã khóa tay)
    s.flush()
    s.add(m.NhanVien(ma="NV01", ho_ten="An", email="an@x.vn", trang_thai="DANG_LAM", nguoi_dung_id=1))        # 1
    s.add(m.NhanVien(ma="NV02", ho_ten="Bình", email="binh@x.vn", trang_thai="DANG_LAM"))                     # 2 không tài khoản
    s.add(m.NhanVien(ma="CEO", ho_ten="Hiếu", email="ceo@x.vn", trang_thai="DANG_LAM", nguoi_dung_id=2))      # 3
    s.add(m.NhanVien(ma="NV04", ho_ten="Cường", email="cu@x.vn", trang_thai="DANG_LAM", nguoi_dung_id=3))     # 4
    s.commit()
    return s


def _nhac(db, nv, tao, han, tt="CHO_LAM", tieu_de="Việc X", thoi_diem=None):
    r = m.NhacViec(nguoi_tao=tao, nhan_vien_id=nv, tieu_de=tieu_de, thoi_diem=thoi_diem or datetime(2026, 10, 28, 8, 0),
                   han_hoan_thanh=han, trang_thai=tt, muc_do="BINH_THUONG")
    db.add(r); db.commit()
    return r


def test_han_khoa(db):
    a = _nhac(db, 1, 3, datetime(2026, 10, 29, 6, 46))                 # hạn TRƯỚC ngày áp dụng → tính 2 ngày từ 05/11 0h
    assert kn.han_khoa(a) == datetime(2026, 11, 7, 0, 0)
    b = _nhac(db, 1, 3, datetime(2026, 11, 6, 16, 0))                  # hạn sau ngày áp dụng → hạn + 2 ngày
    assert kn.han_khoa(b) == datetime(2026, 11, 8, 16, 0)
    assert kn.han_khoa(_nhac(db, 1, 1, datetime(2026, 10, 20, 8, 0))) is None            # tự nhắc mình → không áp dụng
    assert kn.han_khoa(_nhac(db, 1, 3, datetime(2026, 10, 20, 8, 0), tt="DANG_LAM")) is None   # đã phản hồi
    assert kn.han_khoa(_nhac(db, 1, 3, datetime(2026, 10, 20, 8, 0), tt="XONG")) is None
    c = _nhac(db, 1, 3, None, thoi_diem=datetime(2026, 11, 6, 9, 0))   # không đặt hạn → mốc = thời điểm nhắc
    assert kn.han_khoa(c) == datetime(2026, 11, 8, 9, 0)
    q = kn.quy_tac()
    assert q["sau_ngay"] == 2 and q["ap_dung_tu"] == "2026-11-05" and q["thong_bao"] == kn.THONG_BAO


def test_khoa_khong_phan_hoi_va_mo_khoa(db):
    a = _nhac(db, 1, 3, datetime(2026, 10, 29, 6, 46), tieu_de="CIP cụm RO1")       # An — tới giờ khóa 07/11 0h
    _nhac(db, 1, 3, datetime(2026, 11, 6, 16, 0), tieu_de="Việc mới")               # An — chưa tới giờ (08/11 16h)
    e = _nhac(db, 2, 3, datetime(2026, 10, 31, 6, 49), tieu_de="Thay cột MB")        # Bình — không có tài khoản
    _nhac(db, 3, 1, datetime(2026, 10, 20, 8, 0), tieu_de="Việc giao CEO")           # CEO → miễn
    _nhac(db, 1, 1, datetime(2026, 10, 20, 8, 0), tieu_de="Tự nhắc")                 # tự nhắc → không áp dụng
    _nhac(db, 1, 3, datetime(2026, 10, 20, 8, 0), tt="DANG_LAM", tieu_de="Đã nhận")  # đã phản hồi
    c = _nhac(db, 4, 3, datetime(2026, 10, 25, 8, 0), tieu_de="Cường")               # tài khoản đã khóa tay từ trước
    sap = kn.sap_bi_khoa(db, datetime(2026, 11, 6, 12, 0))
    assert {r.tieu_de for r in sap} == {"CIP cụm RO1", "Thay cột MB", "Cường"}       # trưa 06/11: quá hạn, chưa tới giờ khóa
    kq = kn.khoa_khong_phan_hoi(db, NOW)
    assert (kq["so_viec"], kq["da_khoa_tk"], kq["khong_tk"], kq["da_khoa_truoc"], kq["mien"]) == (3, 1, 1, 1, 1)
    assert db.get(m.NguoiDung, 1).trang_thai == "KHOA" and db.get(m.NguoiDung, 2).trang_thai == "HOAT_DONG"
    ks = {k.nhac_viec_id: k for k in db.query(m.NhacViecKhoa).all()}
    assert set(ks) == {a.id, e.id, c.id}
    assert ks[a.id].da_khoa_tai_khoan and ks[a.id].thang == "2026-10" and ks[a.id].nguoi_dung_id == 1
    assert not ks[e.id].da_khoa_tai_khoan and ks[e.id].nguoi_dung_id is None
    assert not ks[c.id].da_khoa_tai_khoan and ks[c.id].nguoi_dung_id == 3                 # chỉ ghi KPI 0
    assert not ks[a.id].chat_da_gui                                                        # DEMO: không gửi thật
    assert [x["tai_khoan"] for x in kq["chi_tiet"]] == ["đã khóa", "không có tài khoản", "đã khóa từ trước"]
    # chạy lại → không khóa / không ghi trùng
    kq2 = kn.khoa_khong_phan_hoi(db, NOW)
    assert kq2["so_viec"] == 0 and db.query(m.NhacViecKhoa).count() == 3
    # câu báo khi đăng nhập: An → đúng câu anh Hiếu chốt; Cường (khóa tay) → câu chung
    assert kn.thong_bao_dang_nhap(db, db.get(m.NguoiDung, 1)).startswith(kn.THONG_BAO)
    assert kn.thong_bao_dang_nhap(db, db.get(m.NguoiDung, 3)) == "Tài khoản đã bị khóa. Liên hệ Admin/CEO để mở lại."
    # danh sách
    ds = kn.danh_sach_khoa(db)
    assert [x["nhan_vien"] for x in ds] == ["Cường", "Bình", "An"] and ds[2]["hieu_luc"] and ds[2]["email"] == "an@x.vn"
    assert kn.danh_sach_khoa(db, nhan_vien_id=1)[0]["tieu_de"] == "CIP cụm RO1" and kn.danh_sach_khoa(db, thang="2026-10")
    # ⭐ KPI tháng 10: An + Bình + Cường = 0 kèm lý do; CEO không bị khóa → KPI theo việc
    kt = {x["ho_ten"]: x for x in kn.kpi_thang(db, "2026-10", NOW)["danh_sach"]}
    assert kt["An"]["kpi"] == 0 and kt["An"]["khoa_n"] == 1 and "khóa do không phản hồi" in kt["An"]["ly_do"]
    assert kt["An"]["so_viec"] == 3 and kt["An"]["so_qua_han"] == 3 and kt["An"]["chua_phan_hoi"] == 1   # «Việc mới» hạn 11; tự nhắc không tính «chưa phản hồi»
    assert kt["Bình"]["kpi"] == 0 and kt["Hiếu"]["kpi"] == 0 and kt["Hiếu"]["khoa_n"] == 0 and kt["Hiếu"]["ly_do"] is None
    assert kn.kpi_thang(db, "2026-11", NOW)["danh_sach"][0]["ho_ten"] == "An" and kn.kpi_thang(db, "2026-11", NOW)["danh_sach"][0]["kpi"] == 0
    assert [x["ho_ten"] for x in kn.kpi_thang(db, "2026-10", NOW, nhan_vien_id=2)["danh_sach"]] == ["Bình"]
    # 🔓 mở khóa: tài khoản hoạt động lại, KPI tháng vẫn 0
    k = kn.mo_khoa(db, ks[a.id].id, db.get(m.NguoiDung, 2), NOW)
    assert k.mo_khoa_luc == NOW and k.mo_khoa_boi == 2 and db.get(m.NguoiDung, 1).trang_thai == "HOAT_DONG"
    assert kn.dang_bi_khoa(db, 1) is None and kn.kpi_thang(db, "2026-10", NOW, nhan_vien_id=1)["danh_sach"][0]["kpi"] == 0
    assert kn.mo_khoa(db, ks[a.id].id, db.get(m.NguoiDung, 2), NOW).mo_khoa_luc == NOW     # mở lần nữa: giữ nguyên
    assert kn.mo_khoa(db, 999, db.get(m.NguoiDung, 2), NOW) is None


def test_tat_tu_dong_va_mo_tay(db):
    a = _nhac(db, 1, 3, datetime(2026, 10, 29, 6, 46))
    settings.nhac_viec_khoa_tu_dong = False
    assert kn.khoa_khong_phan_hoi(db, NOW)["bo_qua"] and db.query(m.NhacViecKhoa).count() == 0
    kq = kn.khoa_khong_phan_hoi(db, NOW, ep=True)                      # nút ▶ Quét ngay vẫn chạy
    assert kq["so_viec"] == 1 and db.get(m.NguoiDung, 1).trang_thai == "KHOA"
    assert kn.dong_khoa_khi_mo_tay(db, 1, 2, NOW) == 1                 # mở tay ở Cấu hình → dòng khóa đóng theo
    db.commit()
    assert kn.dang_bi_khoa(db, 1) is None and db.query(m.NhacViecKhoa).filter_by(nhac_viec_id=a.id).one().mo_khoa_boi == 2
