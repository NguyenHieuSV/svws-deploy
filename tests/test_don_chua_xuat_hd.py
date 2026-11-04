"""
📄 Đơn bán CHƯA XUẤT HÓA ĐƠN (04/11/2026, app/don_chua_xuat_hd.py): bảng ở Bán hàng › Công nợ khách + khối nhắc thứ Hai.
Luật: bỏ Đã xuất HĐ / Hoàn thành / đơn đầu tư; đơn xuất kho mang số tạm vẫn tính; đã thu = công nợ + tạm ứng, hoặc max(cọc, tạm ứng);
đơn chưa có giá trị thì liệt kê nhưng không nhắc. SQLite, bảng phụ tối giản.
"""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import don_chua_xuat_hd as dc
from app import models as m
from app import nhac_qua_han as nq

HOM_NAY = date(2026, 11, 3)


def _ngay(n):
    return HOM_NAY + timedelta(days=n)


def _db():
    e = create_engine("sqlite://")
    for t in (m.DonHang, m.HoaDon, m.CongNo, m.PhieuThuChi, m.DonMua, m.DonMuaCt):
        t.__table__.create(e)
    with e.begin() as c:
        c.exec_driver_sql("CREATE TABLE khach_hang (id INTEGER PRIMARY KEY, ten VARCHAR(200), nguoi_phu_trach INTEGER)")
        c.exec_driver_sql("CREATE TABLE nhan_vien (id INTEGER PRIMARY KEY, ho_ten VARCHAR(120))")
        c.exec_driver_sql("INSERT INTO khach_hang VALUES (1,'II-VI Việt Nam',7),(2,'Coats Phong Phú',NULL)")
        c.exec_driver_sql("INSERT INTO nhan_vien VALUES (7,'Nguyễn B')")
    return sessionmaker(e)()


def _dh(s, id_, so, ngay, tt="MOI", truoc=100_000_000, thue=8_000_000, coc=0, kh=1, **kw):
    s.add(m.DonHang(id=id_, so=so, khach_hang_id=kh, ngay=ngay, trang_thai=tt, tong_tien=Decimal(truoc),
                    tien_thue=Decimal(thue), thanh_toan_coc=Decimal(coc), **kw))


def _nap(s):
    _dh(s, 1, "DA-IIVI-0926-WAF", _ngay(-45), coc=60_000_000)                                   # Mới, cọc ghi trên đơn
    _dh(s, 2, "TM-IIVI-1026-01", _ngay(-10), tt="DANG_THUC_HIEN", truoc=50_000_000, thue=4_000_000, coc=10_000_000)
    s.add(m.PhieuThuChi(id=21, loai="THU", quy_id=1, so_tien=Decimal(70_000_000), da_can_tru=Decimal(0), don_hang_id=2,
                        la_tam_ung=True, trang_thai="DA_DUYET"))                                 # tạm ứng > cọc → lấy số lớn
    _dh(s, 3, "TM-COATS-0926-02", _ngay(-40), tt="DA_XUAT", kh=2)                                # xuất kho → công nợ + HĐ SỐ TẠM
    s.add(m.HoaDon(id=31, loai="BAN", don_hang_id=3, so="TM-COATS-0926-02", tong_tien=Decimal(108_000_000)))
    s.add(m.CongNo(id=301, loai="PHAI_THU", hoa_don_id=31, don_hang_id=3, khach_hang_id=2, so_tien=Decimal(108_000_000),
                   da_thanh_toan=Decimal(20_000_000), so_ct="TM-COATS-0926-02"))
    _dh(s, 4, "DA-X-0826", _ngay(-90), tt="DA_XUAT_HD")                                          # đã xuất hóa đơn → không
    _dh(s, 5, "DA-Y-0826", _ngay(-90), tt="HOAN_THANH")                                          # hoàn thành → không
    _dh(s, 6, "DV-COA-NT-2024", _ngay(-400), loai_don="DAU_TU")                                  # đầu tư – cho thuê → không
    _dh(s, 7, "TM-Z-1026", _ngay(-5), so_hoa_don="0001234")                                      # có số HĐ thật, trạng thái chưa đổi
    _dh(s, 8, "DA-W-0726", _ngay(-100), truoc=0, thue=0)                                         # chưa có giá trị
    s.commit()


def test_so_hd_that():
    assert dc.so_hd_that("0001234", "DA-X-0926")
    assert not dc.so_hd_that("DA-X-0926", "DA-X-0926") and not dc.so_hd_that("dh-12", "DA-X") and not dc.so_hd_that("HD-7", "x")
    assert not dc.so_hd_that("", "x") and not dc.so_hd_that(None, "x")


def test_danh_sach():
    s = _db()
    _nap(s)
    ds = dc.danh_sach(s, HOM_NAY)
    assert [x["id"] for x in ds] == [8, 1, 3, 2, 7]                                 # lâu nhất lên trên; 4 / 5 / 6 bị loại
    x = {d["id"]: d for d in ds}
    a = x[1]
    assert a["so_ngay"] == 45 and a["tong"] == 108e6 and a["da_thu"] == 60e6 and a["nguon_da_thu"] == "cọc trên đơn"
    assert a["con_phai_thu"] == 48e6 and a["khach"] == "II-VI Việt Nam" and a["phu_trach"] == "Nguyễn B" and a["qua_nguong"]
    assert a["cong_no_id"] is None and not a["cong_no_so_tam"] and a["so_hd_san"] is None and a["trang_thai"] == "MOI"
    b = x[2]
    assert b["da_thu"] == 70e6 and b["nguon_da_thu"] == "cả hai" and b["con_phai_thu"] == 0 and not b["qua_nguong"]
    c = x[3]
    assert c["da_xuat_kho"] and c["cong_no_id"] == 301 and c["cong_no_so_tam"] and c["so_hd_san"] is None
    assert c["da_thu"] == 20e6 and c["nguon_da_thu"] == "công nợ" and c["con_phai_thu"] == 88e6 and c["qua_nguong"]
    assert c["khach"] == "Coats Phong Phú" and c["phu_trach"] is None and c["trang_thai"] == "DA_XUAT"
    assert x[7]["so_hd_san"] == "0001234" and x[7]["so_ngay"] == 5 and not x[7]["qua_nguong"]
    assert x[8]["tong"] == 0 and x[8]["con_phai_thu"] == 0 and not x[8]["qua_nguong"]    # chưa có giá trị → không nhắc
    assert dc.tong_hop(ds) == {"so_don": 5, "tong": 378e6, "da_thu": 150e6, "con_phai_thu": 244e6,
                               "qua_nguong": 2, "chua_gia_tri": 1}
    assert dc.danh_sach(_db(), HOM_NAY) == []


def test_qua_nguong_va_khoi_nhac():
    s = _db()
    _nap(s)
    qn = dc.qua_nguong(s, HOM_NAY)
    assert [x["id"] for x in qn] == [1, 3]
    bc = nq.bao_cao(s, HOM_NAY)                                   # không công nợ quá hạn, không PO → chỉ còn khối đơn
    assert [x["id"] for x in bc["don_chua_hd"]] == [1, 3] and bc["tong_don_chua_hd"] == 216e6 and bc["cong_no"] == []
    nd = nq.noi_dung_cong_no(bc)
    assert nd.startswith("💸 *CÔNG NỢ PHẢI THU QUÁ HẠN* — tuần 45/2026 (tính đến 03/11/2026)\nKhông có khoản công nợ nào quá hạn 🎉\n\n"
                         "📄 *ĐƠN BÁN CHƯA XUẤT HÓA ĐƠN quá 30 ngày*: *2 đơn · 216.000.000 đ* (gồm VAT) — "
                         "đã thu 80.000.000 đ · còn phải thu 136.000.000 đ\n")
    assert ("– *DA-IIVI-0926-WAF* · II-VI Việt Nam · ngày 19/09/2026 → *45 ngày* · 108.000.000 đ · đã thu 60.000.000 đ (cọc trên đơn)"
            " · còn 48.000.000 đ · Mới\n") in nd
    assert ("– *TM-COATS-0926-02* · Coats Phong Phú · ngày 24/09/2026 → *40 ngày* · 108.000.000 đ · đã thu 20.000.000 đ (công nợ)"
            " · còn 88.000.000 đ · Đã xuất kho\n") in nd
    assert nd.endswith("ở tab Đơn hàng.")
    bc["don_chua_hd"][0]["so_hd_san"] = "0009999"
    assert "· Mới · ⚠ đã ghi số HĐ 0009999 nhưng trạng thái chưa đổi" in nq.noi_dung_cong_no(bc)
    assert nq.noi_dung_cong_no({"hom_nay": HOM_NAY, "cong_no": [], "tong_cong_no": 0, "po": [], "don_chua_hd": []}) is None
