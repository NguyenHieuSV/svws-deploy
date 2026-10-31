"""
31/10/2026 — mục 4: mọi thêm / sửa / xóa dòng dự toán ghi audit (không chỉ dòng đã mua);
mục 5: BOQ dự án ngang Dự toán hàng bán (mig 163): NCC · mã SP · spec · NSX, điền từ danh mục, ghi ngược danh mục,
nạp mẫu BOQ (nhóm → loại), xuất mẫu 12 cột. SQLite trong bộ nhớ.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import boq_mau as bm
from app import models as m
from app.routers import du_an, ncc
from app.schemas import DuToanVao

NV = SimpleNamespace(id=1, vai_tro=SimpleNamespace(ma="CEO"))
NCC_TEN = "Công ty TNHH Tự Động Hóa Thành Công"


@pytest.fixture()
def ctx(monkeypatch):
    eng = create_engine("sqlite://")
    for t in (m.DuAn, m.DuAnDuToan, m.DuToanBan, m.DuToanBanMuc, m.NhaCungCap, m.SanPhamNcc, m.HangHoa, m.TonKho):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    audit = []
    monkeypatch.setattr(ncc, "ghi_audit", lambda db, uid, hd, bang, bid, cu=None, moi=None: audit.append((hd, bang, bid, cu, moi)))
    monkeypatch.setattr(du_an, "ghi_audit", lambda db, uid, hd, bang, bid, cu=None, moi=None: audit.append((hd, bang, bid, cu, moi)))
    monkeypatch.setattr(ncc, "_dtb_khoa_muc", lambda db, mm, nd=None, xac_nhan=False: None)     # không có PO → không khóa
    monkeypatch.setattr(du_an, "_boq_khoa_map", lambda db, da, rs: {})
    s.add(m.NhaCungCap(ten=NCC_TEN)); s.flush()
    s.add(m.SanPhamNcc(nha_cung_cap_id=1, ten="Tủ điện EDI", ma_sp="TD-EDI", don_vi="bộ", don_gia=Decimal(80_000_000)))
    s.add(m.DuAn(ma="DA-TEST-1026", ten="Dự án thử", chu_dau_tu="Khách"))
    s.add(m.DuToanBan(ma="DT-TEST", ngay=date(2026, 10, 31)))
    s.commit()
    return s, audit


# ---------- mục 4: audit dòng Dự toán hàng bán ----------
def test_audit_dong_du_toan_hang_ban(ctx):
    s, audit = ctx
    r = ncc.dtb_them_muc(1, ncc.DtbMucVao(ten="Bơm cấp", so_luong=2, don_gia=1_000_000), s, NV)
    assert [a[0] for a in audit] == ["THEM_DONG"] and audit[0][4]["ten"] == "Bơm cấp" and audit[0][4]["du_toan"] == "DT-TEST"
    ncc.dtb_sua_muc(r["id"], ncc.DtbMucVao(don_gia=1_200_000), False, s, NV)
    sua = [a for a in audit if a[0] == "SUA_DONG"]
    assert len(sua) == 1 and sua[0][3] == {"don_gia": 1_000_000.0} and sua[0][4]["don_gia"] == 1_200_000.0
    ncc.dtb_sua_muc(r["id"], ncc.DtbMucVao(don_gia=1_200_000), False, s, NV)     # không đổi gì → không ghi thêm
    assert len([a for a in audit if a[0] == "SUA_DONG"]) == 1
    ncc.dtb_xoa_muc(r["id"], False, s, NV)
    xoa = [a for a in audit if a[0] == "XOA_DONG"]
    assert len(xoa) == 1 and xoa[0][3]["ten"] == "Bơm cấp" and xoa[0][3]["du_toan"] == "DT-TEST"


# ---------- mục 5: BOQ dự án ----------
def test_boq_them_sua_noi_danh_muc(ctx):
    s, audit = ctx
    # chọn từ danh mục (san_pham_ncc_id) → máy chủ điền cả dòng; đã có trong danh mục → nối (giá bằng → không hỏi)
    r = du_an.them_du_toan(1, DuToanVao(loai="THIET_BI", ten="", so_luong=1, don_gia=0, san_pham_ncc_id=1), s, NV)
    assert r["ten"] == "Tủ điện EDI" and r["ma_sp"] == "TD-EDI" and r["don_gia"] == 80_000_000 and r["ncc_ten"] == NCC_TEN
    assert r["san_pham_ncc_id"] == 1 and r["nha_cung_cap_id"] == 1 and r["danh_muc"]["trang_thai"] == "DA_LIEN_KET"
    assert [a[0] for a in audit if a[1] == "du_an_du_toan"] == ["THEM_DONG"]
    # nhập tay đủ NCC (đúng tên hồ sơ) + tên mới + giá → tạo sản phẩm mới trong danh mục
    r2 = du_an.them_du_toan(1, DuToanVao(loai="VAT_TU", ten="Van bướm DN100", ncc_ten=NCC_TEN.lower(), so_luong=4,
                                         don_gia=2_500_000, nha_san_xuat="Kitz", spec="PN16"), s, NV)
    assert r2["danh_muc"]["hanh_dong"] == "TAO_MOI" and r2["san_pham_ncc_id"] and r2["nha_cung_cap_id"] == 1
    sp = s.get(m.SanPhamNcc, r2["san_pham_ncc_id"])
    assert sp.ten == "Van bướm DN100" and float(sp.don_gia) == 2_500_000 and sp.nha_san_xuat == "Kitz" and sp.spec == "PN16"
    # sửa dòng: đổi NSX → audit SUA_DONG chỉ các cột đổi; đổi giá dòng đã nối, giá lệch danh mục → trả gia_lech để hỏi
    r3 = du_an.sua_du_toan(r2["id"], DuToanVao(nha_san_xuat="Kitz Japan", don_gia=2_700_000), False, s, NV)
    assert r3["nha_san_xuat"] == "Kitz Japan" and r3["danh_muc"]["gia_lech"]["gia_du_toan"] == 2_700_000
    sua = [a for a in audit if a[0] == "SUA_DONG" and a[1] == "du_an_du_toan"]
    assert len(sua) == 1 and set(sua[0][3]) == {"nha_san_xuat", "don_gia"} and sua[0][4]["du_an"] == "DA-TEST-1026"
    assert float(s.get(m.SanPhamNcc, r2["san_pham_ncc_id"]).don_gia) == 2_500_000      # chưa xác nhận → danh mục giữ giá
    # xác nhận đổi giá danh mục
    k = du_an.boq_cap_nhat_gia_danh_muc(r2["id"], s, NV)
    assert k["gia_moi"] == 2_700_000 and float(s.get(m.SanPhamNcc, r2["san_pham_ncc_id"]).don_gia) == 2_700_000
    # xóa → XOA_DONG
    du_an.xoa_du_toan(r2["id"], False, s, NV)
    assert [a for a in audit if a[0] == "XOA_DONG" and a[1] == "du_an_du_toan"][0][3]["ten"] == "Van bướm DN100"


def test_boq_loai_tu_nhom():
    assert du_an._boq_loai_tu_nhom("THIẾT BỊ CÔNG NGHỆ") == "THIET_BI"
    assert du_an._boq_loai_tu_nhom("ĐƯỜNG ỐNG, PHỤ KIỆN & VAN TAY") == "VAT_TU"
    assert du_an._boq_loai_tu_nhom("CHI PHÍ LẮP ĐẶT") == "CHI_PHI_KHAC"
    assert du_an._boq_loai_tu_nhom("NHÂN CÔNG VẬN HÀNH") == "NHAN_SU"
    assert du_an._boq_loai_tu_nhom("") == "THIET_BI"


def test_boq_nap_mau_va_xuat_mau(ctx):
    s, audit = ctx
    da = s.get(m.DuAn, 1)
    items = [
        {"ma": "A01", "ten": "Tủ điện EDI", "so_luong": 1, "don_gia": 80_000_000, "ncc_ten": NCC_TEN, "ma_sp": "TD-EDI",
         "nhom_ma": "A", "nhom_ten": "THIẾT BỊ CÔNG NGHỆ", "nguon": "Đề xuất"},
        {"ma": "D01", "ten": "Ống uPVC D168", "so_luong": 120, "don_gia": 185_000, "don_vi": "m", "nha_san_xuat": "Bình Minh",
         "nhom_ma": "D", "nhom_ten": "ĐƯỜNG ỐNG, PHỤ KIỆN & VAN TAY", "ncc_ten": "NCC Lạ"},
        {"ma": "G01", "ten": "Lắp đặt", "so_luong": 1, "don_gia": 30_000_000, "nhom_ma": "G", "nhom_ten": "CHI PHÍ LẮP ĐẶT"},
    ]
    kq = du_an._boq_them_muc_mau(s, NV, da, items, "boq.xlsx")
    s.commit()
    assert kq["them"] == 3 and kq["ncc_gan"] == 1 and kq["dm_noi"] == 1 and kq["dm_tao"] == 0 and kq["ncc_la"] == ["NCC Lạ"]
    rows = {x.ten: x for x in s.query(m.DuAnDuToan).filter_by(du_an_id=1).all()}
    assert rows["Tủ điện EDI"].loai == "THIET_BI" and rows["Tủ điện EDI"].san_pham_ncc_id == 1
    assert rows["Ống uPVC D168"].loai == "VAT_TU" and rows["Ống uPVC D168"].ncc_ten == "NCC Lạ" and rows["Ống uPVC D168"].nha_cung_cap_id is None
    assert rows["Lắp đặt"].loai == "CHI_PHI_KHAC" and "BOQ G01" in rows["Lắp đặt"].ghi_chu
    assert len([a for a in audit if a[0] == "THEM_DONG"]) == 3
    # xuất mẫu → đọc lại được: 3 nhóm theo loại, giữ NCC · mã SP
    resp = du_an.boq_mau(1, s, None)
    nhom, ds = bm.doc_boq(resp.body, "x.xlsx")
    assert len(ds) == 3 and {n["ma"] for n in nhom} == {"A", "D", "G"}       # giữ đúng nhóm gốc đã nạp (A · D · G)
    r0 = next(x for x in ds if x["ten"] == "Tủ điện EDI")
    assert r0["ncc_ten"] == NCC_TEN and r0["ma_sp"] == "TD-EDI" and r0["don_gia"] == 80_000_000
