"""
⏰ Nhắc quá hạn hàng tuần (01/11/2026, app/nhac_qua_han.py): công nợ PHẢI THU quá hạn (mốc = hẹn TT / hạn, bỏ Hoàn thành
và đã thu đủ) + PO ĐÃ DUYỆT quá hẹn giao chưa nhận đủ → nội dung tin + nơi gửi (Duyệt chi / Purchasing / nhóm riêng).
SQLite, bảng phụ tối giản theo đúng cột module đọc.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import chat_gateway
from app import models as m
from app import nhac_qua_han as nq
from app.config import settings

HOM_NAY = date(2026, 11, 3)          # thứ Hai


def _ngay(n):
    return HOM_NAY + timedelta(days=n)


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setattr(nq, "hom_nay_vn", lambda: HOM_NAY)
    e = create_engine("sqlite://")
    for t in (m.CongNo, m.DonMua, m.DonMuaCt, m.DonHang, m.HoaDon, m.PhieuThuChi):
        t.__table__.create(e)
    with e.begin() as c:
        c.exec_driver_sql("CREATE TABLE khach_hang (id INTEGER PRIMARY KEY, ten VARCHAR(200), nguoi_phu_trach INTEGER)")
        c.exec_driver_sql("CREATE TABLE nhan_vien (id INTEGER PRIMARY KEY, nguoi_dung_id INTEGER, ho_ten VARCHAR(120))")
        c.exec_driver_sql("CREATE TABLE nguoi_dung (id INTEGER PRIMARY KEY, email VARCHAR(150))")
        c.exec_driver_sql("CREATE TABLE nha_cung_cap (id INTEGER PRIMARY KEY, ten VARCHAR(200))")
        c.exec_driver_sql("CREATE TABLE hang_hoa (id INTEGER PRIMARY KEY, ten VARCHAR(200))")
        c.exec_driver_sql("CREATE TABLE audit_log (id INTEGER PRIMARY KEY, nguoi_dung_id INTEGER, hanh_dong VARCHAR(20), "
                          "bang VARCHAR(60), ban_ghi_id INTEGER, gia_tri_cu TEXT, gia_tri_moi TEXT, thoi_gian TIMESTAMP)")
        c.exec_driver_sql("INSERT INTO khach_hang VALUES (1,'Công ty A',7),(2,'Công ty B',NULL)")
        c.exec_driver_sql("INSERT INTO nhan_vien VALUES (7,70,'Nguyễn B'),(8,80,'Trần C')")
        c.exec_driver_sql("INSERT INTO nguoi_dung VALUES (70,'b@sv.vn'),(80,'c@sv.vn'),(90,'khac@sv.vn')")
        c.exec_driver_sql("INSERT INTO nha_cung_cap VALUES (3,'Hóa chất Miền Nam')")
        c.exec_driver_sql("INSERT INTO hang_hoa VALUES (1,'Hóa chất PAC'),(2,'Van bi 60'),(3,'Bơm định lượng')")
        # PO 101: người lập = bản ghi audit ĐẦU (nd 70), không phải người duyệt sau (nd 90)
        c.exec_driver_sql("INSERT INTO audit_log (id,nguoi_dung_id,hanh_dong,bang,ban_ghi_id) VALUES "
                          "(1,70,'TAO','don_mua',101),(2,90,'DUYET','don_mua',101),(3,80,'TAO','don_mua',105)")
    s = sessionmaker(e)()
    # đơn 9 / 10 đã xuất hóa đơn / hoàn thành → KHÔNG thuộc khối «đơn chưa xuất hóa đơn»
    s.add(m.DonHang(id=9, so="TM-SIC-0826-01", khach_hang_id=1, ngay=date(2026, 8, 20), trang_thai="HOAN_THANH"))
    s.add(m.DonHang(id=10, so="DV-COA-NT-1026", khach_hang_id=2, ngay=date(2026, 10, 5), trang_thai="DA_XUAT_HD"))
    s.add(m.HoaDon(id=5, loai="BAN", so="00123", don_hang_id=9))
    s.commit()
    return s


def _cn(s, id_, **kw):
    base = dict(loai="PHAI_THU", so_tien=Decimal(0), da_thanh_toan=Decimal(0), trang_thai="CHUA_THU", nhac_trang_thai="CHO")
    base.update(kw)
    s.add(m.CongNo(id=id_, **base))


def _po(s, id_, **kw):
    base = dict(so=f"PO-{id_}", nha_cung_cap_id=3, trang_thai="DA_DUYET", ngay=date(2026, 10, 1), tien_hang=0, tien_thue=0,
                tong_tien=0, trang_thai_nhan="CHUA")
    base.update(kw)
    s.add(m.DonMua(id=id_, **base))


def _nap(s):
    _cn(s, 1, don_hang_id=9, so_tien=Decimal(200_000_000), han=_ngay(-45), so_ct="00123")        # khách A qua đơn bán
    _cn(s, 2, khach_hang_id=1, so_tien=Decimal(9e6), han=_ngay(-10), ngay_tt_tiep=_ngay(5))         # đã hẹn TT sau → chưa quá hạn
    _cn(s, 3, khach_hang_id=1, so_tien=Decimal(9e6), han=_ngay(-10), nhac_trang_thai="XONG")       # Hoàn thành → không nhắc
    _cn(s, 4, khach_hang_id=1, so_tien=Decimal(5e6), da_thanh_toan=Decimal(5e6), han=_ngay(-10))   # đã thu đủ
    _cn(s, 5, khach_hang_id=2, so_tien=Decimal(50_000_000), han=_ngay(-100), ma_ban_ngoai="DV-X-0725")
    _cn(s, 6, hoa_don_id=5, so_tien=Decimal(30_000_000), da_thanh_toan=Decimal(10_000_000), han=_ngay(30),
        ngay_tt_tiep=_ngay(-3))                                                                     # hẹn TT đã qua dù hạn còn
    _cn(s, 7, loai="PHAI_TRA", nha_cung_cap_id=3, so_tien=Decimal(9e6), han=_ngay(-50))             # phải trả → không thuộc bản này
    _cn(s, 8, khach_hang_id=1, so_tien=Decimal(9e6))                                                 # không hạn, không hẹn
    _po(s, 101, ngay_hen_giao=_ngay(-10), don_hang_id=9)
    for i, hh in enumerate((1, 2, 3), 1):
        s.add(m.DonMuaCt(id=1010 + i, don_mua_id=101, hang_hoa_id=hh, so_luong=1, don_gia=1000))
    _po(s, 102, ngay_hen_giao=_ngay(-5), trang_thai_nhan="DU")                                      # đã nhận đủ
    _po(s, 103, ngay_hen_giao=_ngay(-5), trang_thai="CHO_DUYET")                                    # chưa duyệt
    _po(s, 104, ngay_hen_giao=_ngay(3))                                                              # chưa tới hẹn
    _po(s, 105, ngay_hen_giao=_ngay(-30), trang_thai_nhan="MOT_PHAN", ma_ban="DV-COA-NT-1026")
    _po(s, 106, ngay_hen_giao=_ngay(-1), trang_thai_nhan=None)                                       # dòng cũ chưa có trạng thái nhận
    _po(s, 107)                                                                                      # không hẹn giao
    s.commit()


def test_cong_no_qua_han(db):
    _nap(db)
    ds = nq.cong_no_qua_han(db)
    assert [x["id"] for x in ds] == [5, 1, 6]                                   # lâu nhất lên trên
    x1 = ds[1]
    assert x1["khach"] == "Công ty A" and x1["phu_trach"] == "Nguyễn B" and x1["ma_ban"] == "TM-SIC-0826-01"
    assert x1["so_hd"] == "00123" and x1["qua_han_ngay"] == 45 and x1["bac"] == "31–60 ngày" and not x1["hen_tt"]
    x6 = ds[2]
    assert x6["hen_tt"] and x6["con_lai"] == 20_000_000 and x6["so_hd"] == "00123" and x6["bac"] == "1–30 ngày"
    assert ds[0]["khach"] == "Công ty B" and ds[0]["phu_trach"] is None and ds[0]["bac"] == "trên 90 ngày"
    bc = nq.bao_cao(db)
    assert bc["tong_cong_no"] == 270_000_000
    nd = nq.noi_dung_cong_no(bc)
    assert "💸 *CÔNG NỢ PHẢI THU QUÁ HẠN* — tuần 45/2026 (tính đến 03/11/2026)" in nd
    assert "Tổng: *3 khoản · 270.000.000 đ* — 1–30 ngày: 1 (20.000.000 đ) · 31–60 ngày: 1 (200.000.000 đ) · trên 90 ngày: 1 (50.000.000 đ)" in nd
    a = nd.index("🏢 *Công ty A* — 2 khoản · 220.000.000 đ · lâu nhất 45 ngày · phụ trách: Nguyễn B")
    b = nd.index("🏢 *Công ty B* — 1 khoản · 50.000.000 đ · lâu nhất 100 ngày\n")                  # không có phụ trách
    assert a < b                                                                   # khách nợ nhiều hơn lên trước
    assert "– TM-SIC-0826-01 · HĐ 00123 · 200.000.000 đ · quá 45 ngày (hạn 19/09/2026)" in nd
    assert "– TM-SIC-0826-01 · HĐ 00123 · 20.000.000 đ · quá 3 ngày (hẹn TT 31/10/2026)" in nd
    assert "– DV-X-0725 · 50.000.000 đ · quá 100 ngày (hạn 26/07/2026)" in nd
    assert nd.endswith("đánh dấu Hoàn thành để ngừng nhắc.")


def test_po_qua_hen(db):
    _nap(db)
    ds = nq.po_qua_hen(db)
    assert [x["id"] for x in ds] == [105, 101, 106]
    assert ds[0]["nhan"] == "nhận một phần" and ds[0]["ma_ban"] == "DV-COA-NT-1026" and ds[0]["nguoi_lap"] == "Trần C"
    assert ds[1]["ma_ban"] == "TM-SIC-0826-01" and ds[1]["hang_hoa"] == "Hóa chất PAC · Van bi 60 +1" and ds[1]["nguoi_lap"] == "Nguyễn B"
    assert ds[2]["nhan"] == "chưa nhận" and ds[2]["hang_hoa"] is None and ds[2]["nguoi_lap"] is None and ds[2]["tre_ngay"] == 1
    nd = nq.noi_dung_po(nq.bao_cao(db), ghi_chu_nhom="_(ghi chú nhóm)_")
    assert "Tổng: *3 PO* — chưa nhận: 2 · nhận một phần: 1 · trễ lâu nhất 30 ngày\n_(ghi chú nhóm)_" in nd
    assert "– *PO-105* · Hóa chất Miền Nam · mã DV-COA-NT-1026 · hẹn 04/10/2026 → trễ *30 ngày* · nhận một phần · lập: Trần C" in nd
    assert "– *PO-101* · Hóa chất Miền Nam · mã TM-SIC-0826-01 · hẹn 24/10/2026 → trễ *10 ngày* · chưa nhận · Hóa chất PAC · Van bi 60 +1 · lập: Nguyễn B" in nd
    assert "– *PO-106* · Hóa chất Miền Nam · hẹn 02/11/2026 → trễ *1 ngày* · chưa nhận\n" in nd


def test_gui_tuan_noi_gui(db, monkeypatch):
    _nap(db)
    gui = []
    monkeypatch.setattr(chat_gateway, "gui_webhook_rieng", lambda url, nd: gui.append((url, nd)) or {"da_gui": True})
    monkeypatch.setattr(settings, "gchat_webhook_duyet_chi", "https://dc")
    monkeypatch.setattr(settings, "gchat_webhook_purchasing", "")
    monkeypatch.setattr(settings, "gchat_webhook_cong_no", "")
    kq = nq.gui_tuan(db, "TAY", "Hiếu")
    assert kq["da_gui"] and kq["cong_no"]["da_gui"] and kq["po"]["da_gui"] and kq["so_cong_no"] == 3 and kq["so_po"] == 3
    assert [u for u, _ in gui] == ["https://dc", "https://dc"]                    # chưa khai Purchasing → PO cũng vào Duyệt chi
    assert "CÔNG NỢ PHẢI THU QUÁ HẠN" in gui[0][1] and gui[0][1].endswith("(gửi tay bởi Hiếu)")
    assert "chưa khai webhook nhóm Purchasing Team" in gui[1][1] and kq["po"]["nhom"].startswith("nhóm Duyệt chi")
    assert kq["cong_no"]["nhom"] == "nhóm Duyệt chi"
    gui.clear()
    monkeypatch.setattr(settings, "gchat_webhook_purchasing", "https://pur")
    monkeypatch.setattr(settings, "gchat_webhook_cong_no", "https://cn")
    kq = nq.gui_tuan(db)
    assert [u for u, _ in gui] == ["https://cn", "https://pur"] and "chưa khai" not in gui[1][1] and "gửi tay" not in gui[0][1]
    assert kq["cong_no"]["nhom"] == "nhóm riêng Công nợ" and kq["po"]["nhom"] == "nhóm Purchasing Team"
    gui.clear()
    for k in ("gchat_webhook_duyet_chi", "gchat_webhook_purchasing", "gchat_webhook_cong_no"):
        monkeypatch.setattr(settings, k, "")
    kq = nq.gui_tuan(db)
    assert not kq["da_gui"] and gui == [] and "GCHAT_WEBHOOK_DUYET_CHI" in kq["cong_no"]["ly_do"]
    assert "GCHAT_WEBHOOK_PURCHASING" in kq["po"]["ly_do"]


def test_gui_tuan_khong_co_gi_thi_khong_gui(db, monkeypatch):
    monkeypatch.setattr(settings, "gchat_webhook_duyet_chi", "https://dc")
    monkeypatch.setattr(chat_gateway, "gui_webhook_rieng", lambda *a: pytest.fail("không được gửi khi không có gì quá hạn"))
    kq = nq.gui_tuan(db)
    assert not kq["da_gui"] and kq["cong_no"]["ly_do"] == "Không có công nợ phải thu quá hạn (và không có đơn chưa xuất hóa đơn quá 30 ngày)"
    assert kq["po"]["ly_do"] == "Không có PO quá hẹn giao" and kq["so_cong_no"] == 0 and kq["so_po"] == 0 and kq["so_don_chua_hd"] == 0


def _don_chua_hd(s, id_, so, ngay, coc=0, truoc=100_000_000, thue=8_000_000):
    s.add(m.DonHang(id=id_, so=so, khach_hang_id=1, ngay=ngay, trang_thai="MOI", tong_tien=Decimal(truoc),
                    tien_thue=Decimal(thue), thanh_toan_coc=Decimal(coc)))


def test_don_chua_xuat_hd_gop_vao_tin_cong_no(db, monkeypatch):
    _nap(db)
    _don_chua_hd(db, 11, "DA-IIVI-0926-WAF", _ngay(-45), coc=30_000_000)
    _don_chua_hd(db, 12, "TM-SIC-1026-02", _ngay(-10), truoc=20_000_000, thue=1_600_000)      # mới 10 ngày → chưa nhắc
    db.commit()
    bc = nq.bao_cao(db)
    assert [x["id"] for x in bc["don_chua_hd"]] == [11] and bc["tong_don_chua_hd"] == 108_000_000
    nd = nq.noi_dung_cong_no(bc)
    assert "🏢 *Công ty A* — 2 khoản · 220.000.000 đ" in nd                                      # phần công nợ giữ nguyên
    assert ("đánh dấu Hoàn thành để ngừng nhắc.\n\n📄 *ĐƠN BÁN CHƯA XUẤT HÓA ĐƠN quá 30 ngày*: *1 đơn · 108.000.000 đ* (gồm VAT)"
            " — đã thu 30.000.000 đ · còn phải thu 78.000.000 đ\n") in nd
    assert ("– *DA-IIVI-0926-WAF* · Công ty A · ngày 19/09/2026 → *45 ngày* · 108.000.000 đ · đã thu 30.000.000 đ (cọc trên đơn)"
            " · còn 78.000.000 đ · Mới\n") in nd
    gui = []
    monkeypatch.setattr(chat_gateway, "gui_webhook_rieng", lambda url, nd_: gui.append((url, nd_)) or {"da_gui": True})
    monkeypatch.setattr(settings, "gchat_webhook_duyet_chi", "https://dc")
    monkeypatch.setattr(settings, "gchat_webhook_purchasing", "")
    monkeypatch.setattr(settings, "gchat_webhook_cong_no", "")
    kq = nq.gui_tuan(db)
    assert kq["so_don_chua_hd"] == 1 and kq["cong_no"]["da_gui"] and "ĐƠN BÁN CHƯA XUẤT HÓA ĐƠN" in gui[0][1]


def test_chi_co_don_chua_hd_van_gui_ban_cong_no(db, monkeypatch):
    _don_chua_hd(db, 11, "DA-IIVI-0926-WAF", _ngay(-31))
    db.commit()
    gui = []
    monkeypatch.setattr(chat_gateway, "gui_webhook_rieng", lambda url, nd_: gui.append((url, nd_)) or {"da_gui": True})
    monkeypatch.setattr(settings, "gchat_webhook_duyet_chi", "https://dc")
    monkeypatch.setattr(settings, "gchat_webhook_purchasing", "")
    monkeypatch.setattr(settings, "gchat_webhook_cong_no", "")
    kq = nq.gui_tuan(db)
    assert kq["so_cong_no"] == 0 and kq["so_don_chua_hd"] == 1 and kq["cong_no"]["da_gui"] and not kq["po"]["da_gui"]
    assert gui[0][1].startswith("💸 *CÔNG NỢ PHẢI THU QUÁ HẠN*") and "Không có khoản công nợ nào quá hạn 🎉" in gui[0][1]
    assert "– *DA-IIVI-0926-WAF* · Công ty A · ngày 03/10/2026 → *31 ngày* · 108.000.000 đ · còn 108.000.000 đ · Mới" in gui[0][1]
