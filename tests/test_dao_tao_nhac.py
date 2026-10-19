"""
Test NHẮC NHÂN VIÊN của Training (bài bắt buộc, hạn, nhắc tay / tự động qua Google Chat) — dùng chung khung với test_dao_tao.py.
KHÔNG cần PostgreSQL và KHÔNG gọi mạng: Google Chat được thay bằng bản giả ghi lại tin gửi đi.
"""
from datetime import timedelta

import pytest
from fastapi import HTTPException

from app import models as m
from app.routers import dao_tao as d
from tests.test_dao_tao import ctx, _them  # noqa: F401  (ctx là fixture)


def _dung_chat(monkeypatch, bat=True):
    """Chat giả: ghi lại các tin gửi đi, không gọi mạng."""
    from app import chat_gateway, nhac_viec_service
    gui = []
    monkeypatch.setattr(chat_gateway, "dang_bat", lambda: bat)
    monkeypatch.setattr(chat_gateway, "lay_chat_provider", lambda: type("P", (), {"che_do": "APP"})())
    monkeypatch.setattr(nhac_viec_service, "gui_toi_nguoi", lambda db, prov, email, nd: gui.append((email, nd)) or {"da_gui": True})
    return gui


def _them_nhan_vien(db):
    """Thêm: C (có tài khoản NV_KT, THIẾU email), D (không có tài khoản), E (tài khoản vai trò CEO, có email)."""
    uc = m.NguoiDung(vai_tro_id=2, email="c@x.vn", mat_khau_hash="x", trang_thai="HOAT_DONG")
    ue = m.NguoiDung(vai_tro_id=1, email="e@x.vn", mat_khau_hash="x", trang_thai="HOAT_DONG")
    db.add_all([uc, ue])
    db.flush()
    db.add_all([m.NhanVien(nguoi_dung_id=uc.id, ma="NV03", ho_ten="Lê Văn C", trang_thai="DANG_LAM"),
                m.NhanVien(ma="NV04", ho_ten="Phạm Thị D", trang_thai="DANG_LAM"),
                m.NhanVien(nguoi_dung_id=ue.id, ma="NV05", ho_ten="Hoàng E", email="e@x.vn", trang_thai="DANG_LAM")])
    db.query(m.NhanVien).filter_by(ma="NV01").one().email = "a@x.vn"
    db.commit()


def _ngay(n):
    return d.gio_hien_tai().date() + timedelta(days=n)


def test_danh_sach_dung_doi_tuong(ctx):
    db, ql, nv, muc = ctx
    _them_nhan_vien(db)
    muc["v"] = "THAO_TAC"
    b = _them(db, ql)
    d.sua_bai(b["id"], d.BaiSua(bat_buoc=True, han_hoan_thanh=_ngay(10)), db, ql)
    r = d._can_nhac_ds(db, db.get(m.TrnBai, b["id"]))
    ten = {x["ten"]: x for x in r["can_nhac"]}
    assert set(ten) == {"Nguyễn Văn A", "Lê Văn C", "Hoàng E"} and r["thieu_tai_khoan"] == ["Phạm Thị D", "Trần Thị B"]
    assert ten["Lê Văn C"]["co_email"] is False
    # A thi chưa đạt → vẫn phải nhắc, kèm điểm; sau đó đạt → hết nhắc
    muc["v"] = "XEM"
    d.ghi_ket_qua(b["id"], d.KetQuaVao(diem=60, so_cau=30, so_dung=18), db, nv)
    x = {y["ten"]: y for y in d._can_nhac_ds(db, db.get(m.TrnBai, b["id"]))["can_nhac"]}["Nguyễn Văn A"]
    assert x["tinh_trang"] == "CHUA_DAT" and x["diem_gan_nhat"] == 60
    d.ghi_ket_qua(b["id"], d.KetQuaVao(diem=90, so_cau=30, so_dung=27), db, nv)
    r = d._can_nhac_ds(db, db.get(m.TrnBai, b["id"]))
    assert "Nguyễn Văn A" not in {y["ten"] for y in r["can_nhac"]} and r["da_xong"] == 1
    # chọn vai trò CEO → chỉ Hoàng E thuộc đối tượng (mã vai trò không tồn tại bị bỏ)
    muc["v"] = "THAO_TAC"
    d.sua_bai(b["id"], d.BaiSua(vai_tro_ap_dung=["CEO", "KHONG_CO"]), db, ql)
    bb = db.get(m.TrnBai, b["id"])
    assert bb.vai_tro_ap_dung == "CEO"
    assert [y["ten"] for y in d._can_nhac_ds(db, bb)["can_nhac"]] == ["Hoàng E"]


def test_nhac_tay_gui_chat_nhat_ky_va_chong_don(ctx, monkeypatch):
    db, ql, nv, muc = ctx
    _them_nhan_vien(db)
    muc["v"] = "THAO_TAC"
    b = _them(db, ql, tieu_de="Thi EC")
    d.sua_bai(b["id"], d.BaiSua(bat_buoc=True, han_hoan_thanh=_ngay(-2)), db, ql)               # đã quá hạn 2 ngày
    gui = _dung_chat(monkeypatch)
    kq = d.nhac_ngay(b["id"], d.NhacVao(), db, ql)
    assert kq["da_gui"] == 2 and kq["thieu_email"] == ["Lê Văn C"] and kq["so_can_nhac"] == 3
    noi_dung = dict(gui)["a@x.vn"]
    assert "Nhắc thi — Thi EC" in noi_dung and "ĐÃ QUÁ HẠN" in noi_dung and "Training" in noi_dung and "Nguyễn Văn A" in noi_dung
    assert db.query(m.TrnNhac).filter_by(ket_qua="OK", nguon="TAY").count() == 2
    kq2 = d.nhac_ngay(b["id"], d.NhacVao(), db, ql)                                             # bấm lại ngay → không nhắn dồn
    assert kq2["da_gui"] == 0 and kq2["bo_qua_gan"] == 2
    xem = d.nhac_xem(b["id"], db, ql)
    assert xem["chat"]["dang_bat"] is True and all("email" not in x for x in xem["can_nhac"])    # xem trước không lộ email
    assert {x["ten"]: x["so_lan_nhac"] for x in xem["can_nhac"]}["Nguyễn Văn A"] == 1
    # chọn riêng một người
    b2 = _them(db, ql, tieu_de="Thi khác")
    d.sua_bai(b2["id"], d.BaiSua(bat_buoc=True), db, ql)
    gui.clear()
    nv_e = db.query(m.NhanVien).filter_by(ma="NV05").one()
    kq3 = d.nhac_ngay(b2["id"], d.NhacVao(nhan_vien_ids=[nv_e.id]), db, ql)
    assert kq3["da_gui"] == 1 and [e for e, _ in gui] == ["e@x.vn"]


def test_nhac_khi_chat_chua_bat(ctx, monkeypatch):
    db, ql, nv, muc = ctx
    _them_nhan_vien(db)
    muc["v"] = "THAO_TAC"
    b = _them(db, ql)
    d.sua_bai(b["id"], d.BaiSua(bat_buoc=True), db, ql)
    _dung_chat(monkeypatch, bat=False)
    kq = d.nhac_ngay(b["id"], d.NhacVao(), db, ql)
    assert kq["da_gui"] == 0 and "chưa được bật" in kq["loi"][0] and db.query(m.TrnNhac).count() == 0
    assert d.nhac_tu_dong_hang_ngay(db).get("bo_qua")


def test_nhac_tu_dong_nhip_va_gioi_han(ctx, monkeypatch):
    db, ql, nv, muc = ctx
    _them_nhan_vien(db)
    muc["v"] = "THAO_TAC"
    b = _them(db, ql)
    d.sua_bai(b["id"], d.BaiSua(bat_buoc=True, han_hoan_thanh=_ngay(30), nhac_tu_dong=True), db, ql)
    bb = db.get(m.TrnBai, b["id"])
    gui = _dung_chat(monkeypatch)

    def lui(ngay):
        for n in db.query(m.TrnNhac).all():
            n.tao_luc = n.tao_luc - timedelta(days=ngay)
        db.commit()

    assert d.nhac_tu_dong_hang_ngay(db)["da_gui"] == 2 and len(gui) == 2                         # lần đầu: A và E (C thiếu email)
    assert d.nhac_tu_dong_hang_ngay(db)["da_gui"] == 0                                           # chạy lặp cùng ngày → không nhắn trùng
    lui(3)
    assert d.nhac_tu_dong_hang_ngay(db)["da_gui"] == 0                                           # còn xa hạn: 7 ngày mới nhắc lại
    lui(5)
    assert d.nhac_tu_dong_hang_ngay(db)["da_gui"] == 2                                           # đủ 8 ngày → nhắc lại
    bb.han_hoan_thanh = _ngay(2)                                                                  # gần hạn → nhịp 2 ngày
    db.commit()
    lui(3)
    assert d.nhac_tu_dong_hang_ngay(db)["da_gui"] == 2
    bb.hien = False                                                                               # bài ẩn → không nhắc
    db.commit()
    lui(9)
    assert d.nhac_tu_dong_hang_ngay(db)["da_gui"] == 0
    bb.hien, bb.nhac_tu_dong = True, False                                                        # tắt nhắc tự động → không nhắc
    db.commit()
    assert d.nhac_tu_dong_hang_ngay(db)["da_gui"] == 0
    bb.nhac_tu_dong = True
    nv_a = db.query(m.NhanVien).filter_by(ma="NV01").one()
    for _ in range(d.TOI_DA_NHAC_TU_DONG):                                                        # đã đủ 8 lần tự động → dừng với người này
        db.add(m.TrnNhac(bai_id=bb.id, nhan_vien_id=nv_a.id, nguon="TU_DONG", ket_qua="OK",
                         tao_luc=d.gio_hien_tai() - timedelta(days=30)))
    db.commit()
    gui.clear()
    d.nhac_tu_dong_hang_ngay(db)
    assert "a@x.vn" not in dict(gui)


def test_can_lam_cua_toi(ctx):
    db, ql, nv, muc = ctx
    muc["v"] = "THAO_TAC"
    b = _them(db, ql, tieu_de="Bắt buộc")
    d.sua_bai(b["id"], d.BaiSua(bat_buoc=True, han_hoan_thanh=_ngay(-1), vai_tro_ap_dung=["NV_KT"]), db, ql)
    muc["v"] = "XEM"
    cl = d.can_lam(db, nv)
    assert [x["bai_id"] for x in cl] == [b["id"]] and cl[0]["so_ngay_con"] == -1 and cl[0]["tinh_trang"] == "CHUA_THI"
    assert d.can_lam(db, ql) == []                                                                # vai trò CEO không thuộc đối tượng
    assert d.ds_bai(db, nv)[0]["can_lam"] is True
    d.ghi_ket_qua(b["id"], d.KetQuaVao(diem=85, so_cau=10, so_dung=8), db, nv)
    assert d.can_lam(db, nv) == [] and d.ds_bai(db, nv)[0]["can_lam"] is False


def test_bai_khong_nguong_chi_can_da_thi(ctx):
    db, ql, nv, muc = ctx
    muc["v"] = "THAO_TAC"
    b = _them(db, ql, diem_dat=None)
    d.sua_bai(b["id"], d.BaiSua(bat_buoc=True), db, ql)
    muc["v"] = "XEM"
    d.ghi_ket_qua(b["id"], d.KetQuaVao(diem=20, so_cau=10, so_dung=2), db, nv)                  # không có ngưỡng đạt → đã thi là xong
    assert d.can_lam(db, nv) == [] and d.ds_bai(db, nv)[0]["can_lam"] is False
