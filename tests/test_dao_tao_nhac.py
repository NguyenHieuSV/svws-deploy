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
    ten = {x["ten"]: x for x in r["ds"]}
    assert set(ten) == {"Nguyễn Văn A", "Trần Thị B", "Lê Văn C", "Phạm Thị D", "Hoàng E"}            # ĐỦ nhân viên đang làm việc
    assert len(r["can_nhac"]) == 5 and r["thieu_tai_khoan"] == ["Phạm Thị D", "Trần Thị B"]
    assert ten["Lê Văn C"]["co_email"] is False and ten["Phạm Thị D"]["co_tai_khoan"] is False and ten["Hoàng E"]["co_tai_khoan"] is True
    # A thi chưa đạt → vẫn phải nhắc, kèm điểm; sau đó đạt → hết nhắc
    muc["v"] = "XEM"
    d.ghi_ket_qua(b["id"], d.KetQuaVao(diem=60, so_cau=30, so_dung=18), db, nv)
    x = {y["ten"]: y for y in d._can_nhac_ds(db, db.get(m.TrnBai, b["id"]))["can_nhac"]}["Nguyễn Văn A"]
    assert x["tinh_trang"] == "CHUA_DAT" and x["diem_gan_nhat"] == 60
    d.ghi_ket_qua(b["id"], d.KetQuaVao(diem=90, so_cau=30, so_dung=27), db, nv)
    r = d._can_nhac_ds(db, db.get(m.TrnBai, b["id"]))
    assert "Nguyễn Văn A" not in {y["ten"] for y in r["can_nhac"]} and r["da_xong"] == 1 and len(r["ds"]) == 5
    assert {y["ten"]: y["tinh_trang"] for y in r["ds"]}["Nguyễn Văn A"] == "XONG"                   # người đã xong vẫn hiện trong danh sách
    # chọn vai trò CEO → chỉ Hoàng E thuộc đối tượng (mã vai trò không tồn tại bị bỏ; người chưa có tài khoản không khớp vai trò)
    muc["v"] = "THAO_TAC"
    d.sua_bai(b["id"], d.BaiSua(vai_tro_ap_dung=["CEO", "KHONG_CO"]), db, ql)
    bb = db.get(m.TrnBai, b["id"])
    assert bb.vai_tro_ap_dung == "CEO"
    r = d._can_nhac_ds(db, bb)
    assert [y["ten"] for y in r["ds"]] == ["Hoàng E"] and r["ngoai_doi_tuong"] == 4
    # chọn TỪNG NHÂN VIÊN: ưu tiên hơn vai trò, kể cả người chưa có tài khoản; id lạ / đã nghỉ bị bỏ
    nghi = m.NhanVien(ma="NV09", ho_ten="Đã Nghỉ", trang_thai="NGHI_VIEC")
    db.add(nghi)
    db.commit()
    id_b = db.query(m.NhanVien).filter_by(ma="NV02").one().id
    id_a = db.query(m.NhanVien).filter_by(ma="NV01").one().id
    d.sua_bai(b["id"], d.BaiSua(nhan_vien_ap_dung=[id_b, id_a, id_a, 9999, nghi.id]), db, ql)
    bb = db.get(m.TrnBai, b["id"])
    assert bb.nhan_vien_ap_dung == f"{id_b},{id_a}"
    r = d._can_nhac_ds(db, bb)
    assert [y["ten"] for y in r["ds"]] == ["Nguyễn Văn A", "Trần Thị B"] and r["ngoai_doi_tuong"] == 3
    d.sua_bai(b["id"], d.BaiSua(nhan_vien_ap_dung=[], vai_tro_ap_dung=[]), db, ql)               # bỏ hết → lại là tất cả
    assert len(d._can_nhac_ds(db, db.get(m.TrnBai, b["id"]))["ds"]) == 5


def test_danh_sach_nhan_vien_de_chon(ctx):
    db, ql, nv, muc = ctx
    _them_nhan_vien(db)
    muc["v"] = "THAO_TAC"
    ds = {x["ten"]: x for x in d.ds_nhan_vien_chon(db, ql)}
    assert len(ds) == 5 and ds["Phạm Thị D"]["co_tai_khoan"] is False and ds["Hoàng E"]["vai_tro"] == "CEO"


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
    assert xem["chat"]["dang_bat"] is True and all("email" not in x for x in xem["nhan_vien"])   # xem trước không lộ email
    assert len(xem["nhan_vien"]) == 5 and xem["so_can_nhac"] == 5                                # hiện ĐỦ nhân viên, kể cả chưa có tài khoản
    assert {x["ten"]: x["so_lan_nhac"] for x in xem["nhan_vien"]}["Nguyễn Văn A"] == 1
    # chọn riêng một người
    b2 = _them(db, ql, tieu_de="Thi khác")
    d.sua_bai(b2["id"], d.BaiSua(bat_buoc=True), db, ql)
    gui.clear()
    nv_e = db.query(m.NhanVien).filter_by(ma="NV05").one()
    kq3 = d.nhac_ngay(b2["id"], d.NhacVao(nhan_vien_ids=[nv_e.id]), db, ql)
    assert kq3["da_gui"] == 1 and [e for e, _ in gui] == ["e@x.vn"]


def test_nhac_phong_chung_mot_tin_gop_khong_neu_diem(ctx, monkeypatch):
    """Chat chế độ WEBHOOK (không nhắn riêng được): MỘT tin gộp vào phòng chung, chỉ ghi tên, KHÔNG nêu điểm, không cần email."""
    from app import chat_gateway
    db, ql, nv, muc = ctx
    _them_nhan_vien(db)
    muc["v"] = "THAO_TAC"
    b = _them(db, ql, tieu_de="Thi EC")
    d.sua_bai(b["id"], d.BaiSua(bat_buoc=True, han_hoan_thanh=_ngay(5)), db, ql)
    muc["v"] = "XEM"
    d.ghi_ket_qua(b["id"], d.KetQuaVao(diem=61.5, so_cau=30, so_dung=18), db, nv)                  # A thi chưa đạt 61,5%
    phong = []

    class Phong:
        che_do = "WEBHOOK"

        def gui_phong(self, nd):
            phong.append(nd)
            return {"da_gui": True}

    monkeypatch.setattr(chat_gateway, "dang_bat", lambda: True)
    monkeypatch.setattr(chat_gateway, "lay_chat_provider", lambda: Phong())
    muc["v"] = "THAO_TAC"
    assert d.nhac_xem(b["id"], db, ql)["chat"]["nhan_rieng"] is False
    kq = d.nhac_ngay(b["id"], d.NhacVao(), db, ql)
    assert kq["kieu"] == "PHONG_CHUNG" and kq["da_gui"] == 3 and kq["thieu_email"] == [] and len(phong) == 1
    tin = phong[0]
    assert "Lê Văn C" in tin and "Hoàng E" in tin and "Chưa đạt" in tin and "Nguyễn Văn A" in tin and "còn 5 ngày" in tin
    assert "61" not in tin and "%" not in tin                                                      # không lộ điểm trong phòng chung
    assert db.query(m.TrnNhac).filter_by(ket_qua="OK").count() == 3
    assert d.nhac_ngay(b["id"], d.NhacVao(), db, ql)["da_gui"] == 0 and len(phong) == 1            # bấm lại → bỏ qua, không đăng thêm
    # tự động cũng gộp một tin
    for n in db.query(m.TrnNhac).all():
        n.tao_luc = n.tao_luc - timedelta(days=9)
    db.commit()
    assert d.nhac_tu_dong_hang_ngay(db)["da_gui"] == 3 and len(phong) == 2


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


def test_nhac_nguoi_chua_co_tai_khoan_duoc_chon_tay(ctx, monkeypatch):
    from app import chat_gateway
    db, ql, nv, muc = ctx
    _them_nhan_vien(db)
    muc["v"] = "THAO_TAC"
    b = _them(db, ql, tieu_de="Thi EC")
    d.sua_bai(b["id"], d.BaiSua(bat_buoc=True), db, ql)
    id_d = db.query(m.NhanVien).filter_by(ma="NV04").one().id
    id_a = db.query(m.NhanVien).filter_by(ma="NV01").one().id
    # Chat APP: nhắn riêng — người chưa có tài khoản chỉ nhận được khi có email (D không có email → báo thiếu email)
    gui = _dung_chat(monkeypatch)
    kq = d.nhac_ngay(b["id"], d.NhacVao(nhan_vien_ids=[id_a, id_d]), db, ql)
    assert kq["da_gui"] == 1 and kq["thieu_email"] == ["Phạm Thị D"]
    db.query(m.NhanVien).filter_by(ma="NV04").one().email = "d@x.vn"
    db.commit()
    kq = d.nhac_ngay(b["id"], d.NhacVao(nhan_vien_ids=[id_d]), db, ql)
    assert kq["da_gui"] == 1 and "chưa có tài khoản app" in dict(gui)["d@x.vn"]
    # Chat WEBHOOK: một tin gộp, có dòng liệt kê người chưa có tài khoản
    phong = []

    class Phong:
        che_do = "WEBHOOK"

        def gui_phong(self, nd):
            phong.append(nd)
            return {"da_gui": True}

    monkeypatch.setattr(chat_gateway, "lay_chat_provider", lambda: Phong())
    id_b = db.query(m.NhanVien).filter_by(ma="NV02").one().id
    kq = d.nhac_ngay(b["id"], d.NhacVao(nhan_vien_ids=[id_b, id_a]), db, ql)                      # A vừa được nhắc → bỏ qua; chỉ B
    assert kq["da_gui"] == 1 and "Chưa có tài khoản app SVWS" in phong[0] and "Trần Thị B" in phong[0]


def test_can_lam_theo_nhan_vien_duoc_chon(ctx):
    db, ql, nv, muc = ctx
    muc["v"] = "THAO_TAC"
    b = _them(db, ql, tieu_de="Chọn người")
    id_a = db.query(m.NhanVien).filter_by(ma="NV01").one().id
    id_b = db.query(m.NhanVien).filter_by(ma="NV02").one().id
    d.sua_bai(b["id"], d.BaiSua(bat_buoc=True, nhan_vien_ap_dung=[id_b]), db, ql)                 # chỉ B (chưa có tài khoản)
    muc["v"] = "XEM"
    assert d.can_lam(db, nv) == [] and d.ds_bai(db, nv)[0]["can_lam"] is False                  # A (user nv) không thuộc đối tượng
    muc["v"] = "THAO_TAC"
    d.sua_bai(b["id"], d.BaiSua(nhan_vien_ap_dung=[id_a]), db, ql)
    muc["v"] = "XEM"
    assert [x["bai_id"] for x in d.can_lam(db, nv)] == [b["id"]] and d.ds_bai(db, nv)[0]["can_lam"] is True
