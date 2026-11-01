"""
📜 Nhật ký hệ thống (01/11/2026, app/routers/nhat_ky.py): tra audit_log theo bảng / hành động / người / bản ghi / khoảng ngày
(giờ VN) / chuỗi trong giá trị cũ-mới; 100 dòng một trang, mới nhất lên trên; tên người (hồ sơ → email → hệ thống);
giờ UTC đổi sang VN; Excel cùng bộ lọc; chỉ CEO / ADMIN. SQLite trong bộ nhớ, bảng phụ tối giản theo đúng cột module đọc.
"""
import io
from datetime import date, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.routers import nhat_ky as nk

# thoi_gian lưu UTC (PostgreSQL TIMESTAMPTZ; SQLite naive coi là UTC) → giờ VN = +7
T = {1: datetime(2026, 10, 31, 17, 30, 0),    # 01/11/2026 00:30:00 VN (qua ngày so với UTC)
     2: datetime(2026, 10, 31, 16, 59, 59),   # 31/10/2026 23:59:59 VN
     3: datetime(2026, 10, 30, 3, 0, 0),      # 30/10/2026 10:00:00 VN
     4: datetime(2026, 10, 29, 1, 0, 0),      # 29/10/2026 08:00:00 VN
     5: datetime(2026, 10, 29, 1, 0, 0)}      # cùng giờ với 4 → id lớn lên trước


@pytest.fixture()
def db():
    e = create_engine("sqlite://")
    m.AuditLog.__table__.create(e)
    with e.begin() as c:
        c.exec_driver_sql("CREATE TABLE nhan_vien (id INTEGER PRIMARY KEY, nguoi_dung_id INTEGER, ho_ten VARCHAR(120))")
        c.exec_driver_sql("CREATE TABLE nguoi_dung (id INTEGER PRIMARY KEY, email VARCHAR(150))")
        c.exec_driver_sql("INSERT INTO nhan_vien VALUES (7,70,'Nguyễn B'),(8,80,'Trần C')")
        c.exec_driver_sql("INSERT INTO nguoi_dung VALUES (70,'b@sv.vn'),(80,'c@sv.vn'),(90,'khac@sv.vn')")
    s = sessionmaker(e)()
    s.add_all([
        m.AuditLog(id=1, nguoi_dung_id=70, hanh_dong="TAO", bang="don_hang", ban_ghi_id=9, thoi_gian=T[1],
                   gia_tri_moi={"so": "TM-SIC-1026", "khach": "Công ty A", "ten": "Bơm định lượng"}),
        m.AuditLog(id=2, nguoi_dung_id=90, hanh_dong="DUYET", bang="don_mua", ban_ghi_id=101, thoi_gian=T[2],
                   gia_tri_moi={"ma_ban": "TM-SIC-1026", "tong": 5000000}),
        m.AuditLog(id=3, nguoi_dung_id=None, hanh_dong="NHAC_TAY", bang="nhac_qua_han", ban_ghi_id=None, thoi_gian=T[3],
                   gia_tri_moi={"so_cong_no": 3}),
        m.AuditLog(id=4, nguoi_dung_id=80, hanh_dong="SUA", bang="don_hang", ban_ghi_id=9, thoi_gian=T[4],
                   gia_tri_cu={"gia": 1}, gia_tri_moi={"gia": 2}),
        m.AuditLog(id=5, nguoi_dung_id=80, hanh_dong="XOA", bang="cong_no", ban_ghi_id=5, thoi_gian=T[5],
                   gia_tri_cu={"ghi_chu": "50% TM_SIC"}),
    ])
    s.commit()
    return s


def _ids(kq):
    return [d["id"] for d in kq["dong"]]


def test_mac_dinh_moi_nhat_len_tren_gio_vn_va_ten_nguoi(db):
    kq = nk.truy_van(db)
    assert kq["tong"] == 5 and kq["trang"] == 1 and kq["so_trang"] == 1 and kq["moi_trang"] == 100
    assert _ids(kq) == [1, 2, 3, 5, 4]                                          # mới nhất lên trên, cùng giờ → id lớn trước
    d = {x["id"]: x for x in kq["dong"]}
    assert d[1]["thoi_gian"] == "01/11/2026 00:30:00" and d[1]["thoi_gian_iso"].endswith("+07:00")
    assert d[2]["thoi_gian"] == "31/10/2026 23:59:59" and d[4]["thoi_gian"] == "29/10/2026 08:00:00"
    assert d[1]["nguoi"] == "Nguyễn B"                                          # họ tên hồ sơ nhân viên
    assert d[2]["nguoi"] == "khac@sv.vn"                                        # không có hồ sơ → email tài khoản
    assert d[3]["nguoi"] == nk.HE_THONG and d[3]["nguoi_dung_id"] is None       # luồng nền
    assert d[4]["gia_tri_cu"] == {"gia": 1} and d[4]["gia_tri_moi"] == {"gia": 2} and d[4]["ban_ghi_id"] == 9
    bl = kq["bo_loc"]
    assert bl["bang"] == ["cong_no", "don_hang", "don_mua", "nhac_qua_han"]
    assert bl["hanh_dong"] == ["DUYET", "NHAC_TAY", "SUA", "TAO", "XOA"]
    assert {"bang": "don_hang", "hanh_dong": "SUA", "so": 1} in bl["cap"] and len(bl["cap"]) == 5
    assert bl["nguoi"][0] == {"id": 80, "ten": "Trần C", "so": 2}               # nhiều vết nhất lên đầu
    assert {"id": 0, "ten": nk.HE_THONG, "so": 1} in bl["nguoi"] and {"id": 90, "ten": "khac@sv.vn", "so": 1} in bl["nguoi"]
    assert "bo_loc" not in nk.truy_van(db, kem_bo_loc=False)


def test_bo_loc_tung_truong(db):
    assert _ids(nk.truy_van(db, bang="don_hang")) == [1, 4]
    assert _ids(nk.truy_van(db, hanh_dong="SUA")) == [4]
    assert _ids(nk.truy_van(db, bang="don_hang", hanh_dong="TAO")) == [1]
    assert _ids(nk.truy_van(db, nguoi_dung_id=80)) == [5, 4]
    assert _ids(nk.truy_van(db, nguoi_dung_id=0)) == [3]                        # 0 = hệ thống (cột NULL)
    assert _ids(nk.truy_van(db, ban_ghi_id=9)) == [1, 4]
    assert _ids(nk.truy_van(db, ban_ghi_id=9, bang="don_mua")) == []


def test_tim_chuoi_trong_gia_tri(db):
    assert _ids(nk.truy_van(db, q="TM-SIC-1026")) == [1, 2]                    # trong gia_tri_moi, bảng khác nhau
    assert _ids(nk.truy_van(db, q="tm-sic-1026")) == [1, 2]                    # không phân biệt hoa thường
    assert _ids(nk.truy_van(db, q="  TM-SIC-1026 ")) == [1, 2]                 # bỏ khoảng trắng thừa
    assert _ids(nk.truy_van(db, q="TM_SIC")) == [5]                            # «_» là ký tự thật, không phải đại diện LIKE
    assert _ids(nk.truy_van(db, q="50%")) == [5]                               # «%» cũng vậy
    assert _ids(nk.truy_van(db, q="ghi_chu")) == [5]                           # tìm được cả theo tên khóa (gia_tri_cu)
    assert _ids(nk.truy_van(db, q="khong-co")) == [] and nk.truy_van(db, q="khong-co")["tong"] == 0
    assert nk.truy_van(db, q="")["tong"] == 5                                   # chuỗi rỗng = không lọc


def test_khoang_ngay_theo_gio_viet_nam(db):
    d1 = date(2026, 11, 1)
    assert _ids(nk.truy_van(db, tu=d1, den=d1)) == [1]                         # 17:30 UTC 31/10 đã là 01/11 VN
    assert _ids(nk.truy_van(db, den=date(2026, 10, 31))) == [2, 3, 5, 4]
    assert _ids(nk.truy_van(db, tu=date(2026, 10, 31), den=date(2026, 10, 31))) == [2]
    assert _ids(nk.truy_van(db, tu=date(2026, 10, 30))) == [1, 2, 3]
    assert _ids(nk.truy_van(db, tu=date(2026, 10, 29), den=date(2026, 10, 29), nguoi_dung_id=80)) == [5, 4]
    with pytest.raises(HTTPException) as e:
        nk.truy_van(db, tu=date(2026, 11, 2), den=date(2026, 11, 1))
    assert e.value.status_code == 422 and "ngược" in e.value.detail
    assert nk.doc_ngay("2026-11-01", "từ") == d1 and nk.doc_ngay("01/11/2026", "từ") == d1
    assert nk.doc_ngay("", "từ") is None and nk.doc_ngay(None, "từ") is None
    with pytest.raises(HTTPException):
        nk.doc_ngay("1/11", "từ")
    # chuyển giờ: có múi giờ thì theo múi, naive coi là UTC
    from datetime import timedelta, timezone
    t = nk.sang_gio_vn(datetime(2026, 10, 31, 20, 0, tzinfo=timezone(timedelta(hours=-5))))   # 01:00 UTC 01/11
    assert t.strftime("%d/%m/%Y %H:%M") == "01/11/2026 08:00"
    assert nk.sang_gio_vn(None) is None


def test_phan_trang(db):
    db.add_all([m.AuditLog(id=100 + i, nguoi_dung_id=70, hanh_dong="SUA", bang="khach_hang", ban_ghi_id=i,
                           thoi_gian=datetime(2026, 10, 1, 0, 0, i % 60), gia_tri_moi={"i": i}) for i in range(230)])
    db.commit()
    kq = nk.truy_van(db)
    assert kq["tong"] == 235 and kq["so_trang"] == 3 and len(kq["dong"]) == 100 and _ids(kq)[:5] == [1, 2, 3, 5, 4]
    kq3 = nk.truy_van(db, trang=3, kem_bo_loc=False)
    assert kq3["trang"] == 3 and len(kq3["dong"]) == 35 and _ids(kq3)[-1] == 100   # dòng cũ nhất ở cuối trang cuối
    assert nk.truy_van(db, trang=99)["trang"] == 3                                 # vượt → kẹp về trang cuối
    assert nk.truy_van(db, trang=0)["trang"] == 1
    assert nk.truy_van(db, bang="khach_hang", trang=2)["so_trang"] == 3 and nk.truy_van(db, bang="cong_no")["so_trang"] == 1


def test_xuat_excel_cung_bo_loc(db):
    from openpyxl import load_workbook
    data = nk.xuat_excel(db, q="TM-SIC-1026")
    wb = load_workbook(io.BytesIO(data))
    ws = wb["Nhật ký"]
    assert ws["A1"].value.startswith("SVWS — NHẬT KÝ HỆ THỐNG — xuất lúc ")
    assert ws["A2"].value == "Bộ lọc: tìm «TM-SIC-1026» — 2 dòng"
    assert [c.value for c in ws[4]] == ["STT", "Thời gian (VN)", "Người", "Tài khoản #", "Hành động", "Bảng", "Bản ghi #",
                                        "Giá trị cũ", "Giá trị mới"]
    r1 = [c.value for c in ws[5]]
    assert r1[:7] == [1, "01/11/2026 00:30:00", "Nguyễn B", 70, "TAO", "don_hang", 9] and r1[7] is None
    assert '"so": "TM-SIC-1026"' in r1[8] and "Bơm định lượng" in r1[8]           # JSON giữ tiếng Việt, không \\u
    assert [c.value for c in ws[6]][:3] == [2, "31/10/2026 23:59:59", "khac@sv.vn"] and ws["A7"].value is None
    assert ws.freeze_panes == "A5" and ws.auto_filter.ref == "A4:I6"
    # bộ lọc theo người + ngày ghi rõ ở A2; hệ thống (0) có tên riêng
    ws2 = load_workbook(io.BytesIO(nk.xuat_excel(db, nguoi_dung_id=80, tu=date(2026, 10, 29), den=date(2026, 10, 31))))["Nhật ký"]
    assert ws2["A2"].value == "Bộ lọc: người: Trần C · từ 29/10/2026 đến 31/10/2026 — 2 dòng"
    assert [c.value for c in ws2[5]][2:8] == ["Trần C", 80, "XOA", "cong_no", 5, '{"ghi_chu": "50% TM_SIC"}']
    ws3 = load_workbook(io.BytesIO(nk.xuat_excel(db, nguoi_dung_id=0)))["Nhật ký"]
    assert ws3["A2"].value == f"Bộ lọc: người: {nk.HE_THONG} — 1 dòng" and ws3["C5"].value == nk.HE_THONG
    assert load_workbook(io.BytesIO(nk.xuat_excel(db)))["Nhật ký"]["A2"].value == "Bộ lọc: toàn bộ — 5 dòng"


def test_chi_ceo_admin_moi_xem():
    """Cả hai route đều gắn chi_vai_tro('CEO','ADMIN') — không hard-code theo mức module."""
    duong = {}
    for r in nk.router.routes:
        cho_phep = set()
        for dep in r.dependant.dependencies:
            fn = dep.call
            if "cho_phep" in getattr(fn, "__code__", None).co_freevars if getattr(fn, "__code__", None) else False:
                cho_phep |= fn.__closure__[fn.__code__.co_freevars.index("cho_phep")].cell_contents
        duong[r.path] = cho_phep
    assert duong == {"/nhat-ky": {"CEO", "ADMIN"}, "/nhat-ky/xuat": {"CEO", "ADMIN"}}
