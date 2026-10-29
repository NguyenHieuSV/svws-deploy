"""
Báo giá gửi khách mang đủ thông tin sản phẩm (29/10/2026): mã SP · nhà sản xuất · spec in cho khách (PDF / bản in),
nhà cung cấp chỉ nội bộ; tạo ngược dự toán từ báo giá giữ các thông tin này; giao diện có ô nhập + tìm danh mục Sản phẩm NCC.
"""
import os

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import bao_gia_ks as bk
from app import models as m
from app.bao_gia_pdf import mo_ta_day_du, tao_bao_gia_pdf

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_mo_ta_day_du():
    it = {"mo_ta": "Tủ inox & cửa kính", "ma_sp": "TD-EDI<1>", "nha_san_xuat": "Schneider", "spec": "380V; IP54", "ncc_ten": "NCC X"}
    s = mo_ta_day_du(it)
    assert "Tủ inox &amp; cửa kính" in s and "Code: TD-EDI&lt;1&gt;" in s and "Brand: Schneider" in s and "380V; IP54" in s
    assert "NCC X" not in s                                                     # nhà cung cấp không in cho khách
    assert mo_ta_day_du({"mo_ta": "chỉ mô tả"}) == "chỉ mô tả"
    assert mo_ta_day_du({}) == ""
    assert mo_ta_day_du({"nha_san_xuat": "Ebara"}) == "<font size='7' color='#5B7186'>Brand: Ebara</font>"


def test_pdf_sinh_duoc_voi_thong_tin_san_pham(tmp_path):
    d = {"so": "TM-TEST-1026-01", "ngay": "2026-10-29", "khach_ten": "Khach", "vat_pct": 8,
         "items": [{"ten": "Bom", "mo_ta": "Bom ly tam", "ma_sp": "CDX 120/20", "nha_san_xuat": "Ebara", "spec": "Q=10 m3/h; H=20 m",
                    "so_luong": 1, "don_gia": 10_000_000, "vat_pct": 8, "ncc_ten": "NCCNOIBO"}]}
    p = tao_bao_gia_pdf(str(tmp_path / "bg.pdf"), d, font_path="/khong/co.ttf", font_bold_path="/khong/co.ttf")
    assert os.path.getsize(p) > 1500
    try:
        from pypdf import PdfReader
    except ImportError:                                                         # không có pypdf → chỉ kiểm tra sinh được file
        return
    txt = "".join(pg.extract_text() for pg in PdfReader(p).pages)
    assert "CDX 120/20" in txt and "Ebara" in txt and "H=20 m" in txt and "NCCNOIBO" not in txt


def test_giao_dien_co_o_thong_tin_san_pham():
    with open(os.path.join(GOC, "svws_app.html"), encoding="utf-8") as f:
        s = f.read()
    assert "function _bgfInfoRow(" in s and "function bgfSpChon(" in s and "function _bgMoTaIn(" in s
    assert s.count("${_bgMoTaIn(it,e)}") == 3                                   # bảng chính · tùy chọn · phụ lục kỹ thuật
    assert 'ma_sp:x.ma_sp||""' in s and 'ncc_ten:x.ncc_ten||""' in s          # tạo báo giá từ dự toán mang theo


# ---------- tạo ngược dự toán từ báo giá giữ thông tin sản phẩm ----------
@pytest.fixture()
def db(monkeypatch):
    eng = create_engine("sqlite://")
    for t in (m.BaoGiaForm, m.DuToanBan, m.DuToanBanMuc, m.NhaCungCap, m.SanPhamNcc):
        t.__table__.create(eng)
    with eng.begin() as c:                                                      # bảng tối giản (model có kiểu PostgreSQL)
        c.exec_driver_sql("CREATE TABLE hang_hoa (id INTEGER PRIMARY KEY, ten VARCHAR(200), don_vi VARCHAR(20))")
        c.exec_driver_sql("CREATE TABLE khach_hang (id INTEGER PRIMARY KEY, ma VARCHAR(20), ten VARCHAR(200))")
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    from app.config import settings
    for k, v in (("bg_bien_thiet_bi", 15.0), ("bg_bien_vat_tu", 25.0), ("bg_bien_nhan_cong", 30.0), ("bg_chi_phi_chung", 5.0)):
        monkeypatch.setattr(settings, k, v)
    monkeypatch.setattr(bk, "tim_du_toan", lambda db_, bgf: None)
    import app.audit as au; monkeypatch.setattr(au, "ghi_audit", lambda *a, **k: None)
    import app.ma_code as mc; monkeypatch.setattr(mc, "bat_buoc", lambda ma, nd, ep, nhan="": ma)
    s.add(m.NhaCungCap(ten="NCC Thật")); s.flush()
    s.add(m.SanPhamNcc(nha_cung_cap_id=1, ten="Bơm định lượng", ma_sp="PF-10", don_gia=5_000_000)); s.commit()
    return s


def test_tao_nguoc_du_toan_giu_thong_tin_san_pham(db):
    nd = {"so": "TM-SP-1026-01", "ngay": "2026-10-29", "tieu_de": "Thử", "vat_pct": 8, "items": [
        {"ten": "Bơm định lượng", "so_luong": 1, "don_gia": 8_000_000, "gia_von": 5_000_000, "nhom": "THIET_BI", "mo_ta": "0–10 l/h",
         "ma_sp": "PF-10", "spec": "230V", "nha_san_xuat": "Pulsafeeder", "ncc_ten": "NCC Thật", "nha_cung_cap_id": 1, "san_pham_ncc_id": 1},
        {"ten": "Ống PVC", "so_luong": 10, "don_gia": 20_000, "nhom": "VAT_TU", "nha_cung_cap_id": 99, "san_pham_ncc_id": "x"},   # id lạ → bỏ
    ]}
    b = m.BaoGiaForm(so="TM-SP-1026-01", noi_dung=nd, trang_thai="NHAP"); db.add(b); db.commit()

    class _Nd:
        id = 1
        vai_tro = type("VT", (), {"ma": "CEO"})()

    r = bk.tao_du_toan_tu_bao_gia(db, b, _Nd())
    assert r["so_dong"] == 2
    rows = {x.ten: x for x in db.query(m.DuToanBanMuc).filter_by(du_toan_id=r["du_toan_id"]).all()}
    bom = rows["Bơm định lượng"]
    assert bom.ma_sp == "PF-10" and bom.spec == "230V" and bom.nha_san_xuat == "Pulsafeeder" and bom.ncc_ten == "NCC Thật"
    assert bom.nha_cung_cap_id == 1 and bom.san_pham_ncc_id == 1 and bom.quy_cach == "0–10 l/h"
    ong = rows["Ống PVC"]
    assert ong.nha_cung_cap_id is None and ong.san_pham_ncc_id is None and ong.ma_sp is None and ong.ncc_ten is None
