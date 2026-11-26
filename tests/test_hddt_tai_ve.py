"""
⬇ TỰ TẢI hóa đơn theo link / mã tra cứu của cổng HĐĐT (26/11/2026, mig 171): app/hddt_tai_ve.py + ke_toan_quy._hdc_tu_tai.
Cổng giả qua tham số `lay=` (không gọi mạng); SQLite trong bộ nhớ; file lưu vào thư mục tạm.
"""
import io
import zipfile
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import hddt_tai_ve as tv
from app import models as m
from app.hddt_doc_nhan import doc_nhan
from app.routers import ke_toan_quy as kq

XML = """<?xml version="1.0" encoding="UTF-8"?>
<HDon><DLHDon Id="x"><TTChung><PBan>2.0.1</PBan><THDon>Hóa đơn giá trị gia tăng</THDon><KHMSHDon>1</KHMSHDon>
<KHHDon>C26TTT</KHHDon><SHDon>{so}</SHDon><NLap>2026-11-05</NLap></TTChung>
<NDHDon><NBan><Ten>CÔNG TY TNHH TM - SX CƠ KHÍ TUẤN TÀI</Ten><MST>{mst}</MST></NBan>
<NMua><Ten>CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT</Ten><MST>0303620066</MST></NMua>
<DSHHDVu><HHDVu><THHDVu>Gia công bồn inox 304</THHDVu><SLuong>1</SLuong><DGia>9700000</DGia><ThTien>9700000</ThTien><TSuat>8%</TSuat></HHDVu></DSHHDVu>
<TToan><TgTCThue>9700000</TgTCThue><TgTThue>776000</TgTThue><TgTTTBSo>{tong}</TgTTTBSo></TToan></NDHDon></DLHDon></HDon>"""
PDF = b"%PDF-1.4\n%fake hoa don\n" + b"0" * 300
HTML = b"<!DOCTYPE html><html><body>Nhap ma xac minh <a href='/tai-xml-that?ma=ABC12345'>Tai XML</a><a href='/style.css'>x</a></body></html>"


def _xml(so="277", mst="3703058418", tong="10476000"):
    return XML.format(so=so, mst=mst, tong=tong).encode("utf-8")


# ---------------------------------------------------------------- module tải ----------------------------------------------------------------
def test_chi_cong_hddt_duoc_phep():
    assert tv.kiem_url("https://www.meinvoice.vn/tra-cuu/?sc=ABC") is None
    assert tv.kiem_url("http://3703058418hd.easyinvoice.com.vn/tra-cuu?ma=X") is None
    for xau in ("https://evil.example.com/meinvoice.vn/x", "https://meinvoice.vn.evil.com/x", "ftp://www.meinvoice.vn/x",
                "https://www.meinvoice.vn:8443/x", "https://user:pw@www.meinvoice.vn/x", "http://127.0.0.1/x",
                "http://169.254.169.254/latest/meta-data", "file:///etc/passwd", ""):
        assert tv.kiem_url(xau) is not None, xau


def test_ung_vien_theo_cong():
    u = tv.ung_vien("https://www.meinvoice.vn/tra-cuu/?sc=aBc123XYZ", "ABC123XYZ")
    assert u[0] == "https://www.meinvoice.vn/tra-cuu/DownloadHandler.ashx?Type=xml&Code=aBc123XYZ"      # mã lấy từ link, giữ hoa/thường
    assert "Type=pdf" in u[1] and u[-1] == "https://www.meinvoice.vn/tra-cuu/?sc=aBc123XYZ"
    # thư MISA chỉ có mã, không có link → vẫn tải theo mã
    assert tv.ung_vien(None, "M4TR4CUU", "no-reply@meinvoice.vn")[0].endswith("Type=xml&Code=M4TR4CUU")
    assert tv.ung_vien(None, "M4TR4CUU", "ketoan@ncc.vn") == []
    e = tv.ung_vien("http://3703058418hd.easyinvoice.com.vn/tra-cuu?ma=7UT2SH9WV")
    assert e == ["http://3703058418hd.easyinvoice.com.vn/tai-xml?ma=7UT2SH9WV", "http://3703058418hd.easyinvoice.com.vn/tai-pdf?ma=7UT2SH9WV",
                 "http://3703058418hd.easyinvoice.com.vn/tra-cuu?ma=7UT2SH9WV"]
    assert tv.ung_vien("https://la.example.com/hoadon?ma=1") == []


def test_nhan_dang_theo_chu_ky_file():
    assert tv.nhan_dang(PDF) == "pdf" and tv.nhan_dang(_xml()) == "xml" and tv.nhan_dang(HTML) == "html"
    assert tv.nhan_dang(b"") is None and tv.nhan_dang(b"khong phai file") is None
    assert tv.nhan_dang(b"\xef\xbb\xbf<HDon><SHDon>1</SHDon></HDon>") == "xml"


def test_tai_xml_roi_pdf_va_do_link_trong_trang():
    goi = []

    def lay(url):
        goi.append(url)
        if "Type=xml" in url:
            return _xml(), "application/octet-stream", url
        if "Type=pdf&Viewer" in url:
            return PDF, "text/plain", url                    # không tin Content-Type, nhận theo chữ ký file
        return b"", "", url
    k = tv.tai_hoa_don("https://www.meinvoice.vn/tra-cuu/?sc=ABC12345", lay=lay)
    assert k["ok"] and [t["loai"] for t in k["tep"]] == ["xml", "pdf"] and len(goi) == 2      # đủ XML + PDF thì dừng

    def lay2(url):                                           # cổng chỉ trả trang web có link tải
        if "tai-xml-that" in url:
            return _xml(), "text/xml", url
        return HTML, "text/html", url
    k2 = tv.tai_hoa_don("https://tracuu.vnpt-invoice.com.vn/x?id=1", lay=lay2)
    assert k2["ok"] and k2["tep"][0]["loai"] == "xml" and any(x["kq"] == "html" for x in k2["da_thu"])


def test_khong_tai_duoc_thi_neu_ly_do():
    k = tv.tai_hoa_don("https://la.example.com/hd?ma=1", "MA1")
    assert not k["ok"] and k["ho_tro"] is False and "chưa nằm trong danh sách" in k["ly_do"]
    k2 = tv.tai_hoa_don("https://www.meinvoice.vn/tra-cuu/?sc=ABC12345", lay=lambda u: (HTML.replace(b"tai-xml-that", b"x"), "text/html", u))
    assert not k2["ok"] and k2["ho_tro"] is True and "mã xác minh" in k2["ly_do"]

    def hong(u):
        raise ValueError("cổng trả lỗi HTTP 500")
    k3 = tv.tai_hoa_don("https://www.meinvoice.vn/tra-cuu/?sc=ABC12345", lay=hong)
    assert not k3["ok"] and "HTTP 500" in k3["ly_do"]
    k4 = tv.tai_hoa_don("https://www.meinvoice.vn/tra-cuu/?sc=ABC12345", lay=lambda u: (b"", "", u))
    assert not k4["ok"] and "không trả file" in k4["ly_do"]


def test_goi_zip_lay_xml_va_pdf():
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("hoadon.xml", _xml())
        z.writestr("hoadon.pdf", PDF)
        z.writestr("ghi-chu.txt", "x")
    k = tv.tai_hoa_don("https://www.meinvoice.vn/tra-cuu/?sc=ABC12345", lay=lambda u: (b.getvalue(), "application/zip", u))
    assert k["ok"] and [t["loai"] for t in k["tep"]] == ["xml", "pdf"]


def test_chuyen_huong_ra_ngoai_bi_chan(monkeypatch):
    import urllib.error

    class _Mo:
        def open(self, req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 302, "Found", {"Location": "http://169.254.169.254/latest"}, None)
    monkeypatch.setattr(tv.urllib.request, "build_opener", lambda *a: _Mo())
    # conftest thay _lay_http bằng bản «tắt mạng» và giữ bản thật ở _lay_http_goc
    with pytest.raises(ValueError) as e:
        tv._lay_http_goc("https://www.meinvoice.vn/tra-cuu/DownloadHandler.ashx?Type=xml&Code=A")
    assert "chưa nằm trong danh sách" in str(e.value)


def test_ma_tra_cuu_giu_nguyen_hoa_thuong():
    nd = "CÔNG TY A, Mã số thuế 0101010101 vừa phát hành hóa đơn\nSố hóa đơn: 12\nTổng tiền thanh toán: 1,080,000 VND\nMã tra cứu: aBc_9Zx7Q\n"
    assert doc_nhan("Hóa đơn điện tử số 12", nd)["ma_tra_cuu"] == "aBc_9Zx7Q"


# ---------------------------------------------------------------- điền dòng hàng chờ ----------------------------------------------------------------
def _raw(con, model, pk="id"):
    from sqlalchemy import Integer, Numeric
    kieu = lambda c: ("INTEGER PRIMARY KEY" if c.name == pk else "NUMERIC" if isinstance(c.type, Numeric)   # noqa: E731
                      else "INTEGER" if isinstance(c.type, Integer) else "TEXT")
    con.exec_driver_sql(f"CREATE TABLE {model.__tablename__} ({', '.join(f'{c.name} {kieu(c)}' for c in model.__table__.columns)})")


@pytest.fixture()
def db(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    for k in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.delenv(k, raising=False)
    eng = create_engine("sqlite://")
    m.KtHoaDonCho.__table__.create(eng)
    with eng.begin() as c:
        for t in (m.NhaCungCap, m.TepDinhKem, m.AuditLog):
            _raw(c, t)
        c.exec_driver_sql("INSERT INTO nha_cung_cap (id, ten, ma_so_thue) VALUES (7, 'Cơ khí Tuấn Tài', '3703058418')")
    return sessionmaker(eng)()


def _dong(s, id_=1, tong=0, so="277", **kw):
    r = m.KtHoaDonCho(id=id_, tu_email="hoadon-noreply@easyinvoice.vn", so_hoa_don=so, tong_tien=tong, tien_truoc_thue=0, thue_suat=8,
                      trang_thai="CHO_XAC_NHAN", link_tra_cuu="http://3703058418hd.easyinvoice.com.vn/tra-cuu?ma=7UT2SH9WV",
                      ma_tra_cuu="7UT2SH9WV", nguon_doc="AI", tai_lan=0, **kw)
    s.add(r); s.commit()
    return r


def _lay_xml_pdf(url):
    if "tai-xml" in url:
        return _xml(), "application/xml", url
    if "tai-pdf" in url:
        return PDF, "application/pdf", url
    return HTML, "text/html", url


def test_dong_0_dong_duoc_dien_tien_tu_xml_va_luu_file(db):
    r = _dong(db)
    k = kq._hdc_tu_tai(db, r, None, lay=_lay_xml_pdf)
    db.commit()
    assert k["ok"] and k["dien_tien"] and k["nguon"] == "XML"
    assert (int(r.tong_tien), int(r.tien_truoc_thue), int(r.thue_suat)) == (10476000, 9700000, 8)
    assert r.ngay_hd == date(2026, 11, 5) and r.ky_hieu == "1C26TTT" and r.ncc_mst == "3703058418" and r.nha_cung_cap_id == 7
    assert r.nguon_doc == "XML" and r.tai_tt == "OK" and r.tai_lan == 1 and r.mo_ta.startswith("📄 tiền theo file XML")
    tep = kq._hdc_tep(db, [r.id])[r.id]
    assert [t["loai"] for t in tep] == ["HDDT_XML", "HDDT_PDF"] and tep[0]["ten_file"] == "HD_277_1C26TTT.xml"
    t0 = db.get(m.TepDinhKem, tep[0]["id"])
    assert open(t0.duong_dan, "rb").read() == _xml()
    assert kq._hdc_can_tu_tai(r) is False                       # đã có file → không tải lại tự động
    assert db.query(m.AuditLog).filter_by(hanh_dong="TU_TAI_HDC").count() == 1


def test_khong_ghi_de_tien_hop_le_chi_canh_bao(db):
    r = _dong(db, tong=9_999_000)
    r.tien_truoc_thue = 9_258_333
    db.commit()
    k = kq._hdc_tu_tai(db, r, None, lay=_lay_xml_pdf)
    assert k["ok"] and not k["dien_tien"] and "chưa đổi" in k["canh_bao"] and int(r.tong_tien) == 9_999_000
    assert r.tai_tt == "OK" and "⚠" in r.tai_ghi_chu


def test_vat_uoc_duoc_thay_bang_so_that_khi_tong_khop(db):
    r = _dong(db, tong=10_476_000, mo_ta="⚠ VAT ước 8% từ tổng — kiểm tra lại · bồn inox")
    r.tien_truoc_thue = 9_700_100
    db.commit()
    kq._hdc_tu_tai(db, r, None, lay=_lay_xml_pdf)
    assert int(r.tien_truoc_thue) == 9_700_000 and "VAT ước" not in r.mo_ta and r.mo_ta.startswith("📄 VAT theo file XML")


def test_file_la_hoa_don_so_khac_thi_khong_dung(db):
    r = _dong(db, so="999")
    k = kq._hdc_tu_tai(db, r, None, lay=_lay_xml_pdf)
    assert not k["ok"] and "hóa đơn số 277" in k["ly_do"] and int(r.tong_tien) == 0
    assert r.tai_tt == "LOI" and kq._hdc_tep(db, [r.id]) == {}
    r2 = _dong(db, id_=2, so="000277", ncc_mst="0101010101")            # cùng số nhưng bên bán khác MST
    k2 = kq._hdc_tu_tai(db, r2, None, lay=_lay_xml_pdf)
    assert not k2["ok"] and "MST 3703058418" in k2["ly_do"]


def test_chay_thu_khong_ghi_gi(db):
    r = _dong(db)
    k = kq._hdc_tu_tai(db, r, None, thu=True, lay=_lay_xml_pdf)
    assert k["ok"] and k["doc"]["so_tien"] == 10476000.0 and k["tep"][0]["loai"] == "xml"
    assert int(r.tong_tien) == 0 and r.tai_tt is None and (r.tai_lan or 0) == 0 and kq._hdc_tep(db, [r.id]) == {}


def test_cong_chua_ho_tro_va_gioi_han_so_lan(db):
    r = _dong(db)
    r.link_tra_cuu, r.ma_tra_cuu = "https://hoadon.cong-la.vn/tra-cuu?ma=1", None
    db.commit()
    k = kq._hdc_tu_tai(db, r, None)
    assert not k["ok"] and r.tai_tt == "KHONG_HT" and kq._hdc_can_tu_tai(r) is False
    r2 = _dong(db, id_=2)

    def hong(u):
        raise ValueError("cổng trả lỗi HTTP 503")
    for i in range(3):
        assert kq._hdc_can_tu_tai(r2) is True
        kq._hdc_tu_tai(db, r2, None, lay=hong)
    assert r2.tai_tt == "LOI" and r2.tai_lan == 3 and kq._hdc_can_tu_tai(r2) is False and "HTTP 503" in r2.tai_ghi_chu


def test_chi_co_pdf_thi_nho_ai_khi_dong_con_thieu(db, monkeypatch):
    import app.ai_gateway as ag
    goi = []
    monkeypatch.setattr(ag, "doc_hoa_don_tep", lambda d, ct, fn, goi_y=None: (goi.append(fn) or
                        {"so_hoa_don": "277", "so_tien": 10476000, "tien_truoc_thue": 9700000, "tien_thue": 776000, "ngay": "2026-11-05"}))
    r = _dong(db)
    k = kq._hdc_tu_tai(db, r, None, lay=lambda u: ((PDF, "application/pdf", u) if "tai-pdf" in u else (b"", "", u)))
    assert k["ok"] and k["nguon"] == "PDF" and int(r.tong_tien) == 10476000 and r.nguon_doc == "PDF" and goi == ["hoa_don.pdf"]
    r2 = _dong(db, id_=2, tong=10_476_000, ngay_hd=date(2026, 11, 5))    # dòng đã đủ số liệu → chỉ lưu PDF, không tốn AI
    k2 = kq._hdc_tu_tai(db, r2, None, lay=lambda u: ((PDF, "application/pdf", u) if "tai-pdf" in u else (b"", "", u)))
    assert k2["ok"] and k2["nguon"] is None and len(goi) == 1 and kq._hdc_tep(db, [2])[2][0]["loai"] == "HDDT_PDF"


class _Nd:
    id = None


def test_endpoint_mot_dong_va_hang_loat(db, monkeypatch):
    monkeypatch.setattr(tv, "_lay_http", _lay_xml_pdf)
    _dong(db, id_=1)                               # thiếu tiền → làm trước
    _dong(db, id_=2, tong=10_476_000, so="277")
    r3 = _dong(db, id_=3)
    r3.link_tra_cuu = r3.ma_tra_cuu = None
    db.commit()
    with pytest.raises(HTTPException) as e:
        kq.tu_tai_hoa_don_cho(3, False, db, _Nd())
    assert e.value.status_code == 400
    thu = kq.tu_tai_hoa_don_cho(1, True, db, _Nd())
    assert thu["ok"] and thu["tong_tien"] == 0
    loat = kq.tu_tai_hoa_don_cho_loat(8, db, _Nd())
    assert (loat["da_xet"], loat["tai_duoc"], loat["dien_tien"], loat["con_lai"]) == (2, 2, 1, 0)
    assert loat["chi_tiet"][0]["id"] == 1
    assert kq.tu_tai_hoa_don_cho_loat(8, db, _Nd())["da_xet"] == 0          # đã có file → không tải lại
    tep = kq._hdc_tep(db, [1, 2, 3])
    assert sorted(tep) == [1, 2] and len(tep[1]) == 2
    t1 = db.get(m.TepDinhKem, tep[1][0]["id"])
    assert kq.tai_tep_hoa_don_cho(t1.id, db, None) is not None             # mở lại được file đã tải
