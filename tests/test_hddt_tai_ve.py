"""
⬇ TỰ TẢI hóa đơn theo link / mã tra cứu của cổng HĐĐT (mig 171; viết lại 27/11/2026 theo cách tải THẬT đã kiểm chứng):
  • MISA meInvoice: POST tra-cuu/GetInvoiceDataByTransactionID theo mã → JSON, `data` = XML hóa đơn;
  • EasyInvoice: link «/Invoice/ViewFromEmail?token=…» → token trên trang → /Invoice/DownloadXML → /Invoice/Download, PDF /Invoice/DownloadPdf.
Cổng giả qua tham số `phien=` (không gọi mạng); SQLite trong bộ nhớ; file lưu vào thư mục tạm.
"""
import io
import json
import urllib.parse
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
<HDon><DLHDon Id="x"><TTChung><PBan>2.1.0</PBan><THDon>Hóa đơn giá trị gia tăng</THDon><KHMSHDon>1</KHMSHDon>
<KHHDon>C26TYY</KHHDon><SHDon>{so}</SHDon><NLap>2026-10-31</NLap></TTChung>
<NDHDon><NBan><Ten>Công ty TNHH Thương Mại NINOL</Ten><MST>{mst}</MST></NBan>
<NMua><Ten>CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT</Ten><MST>0303620066</MST></NMua>
<DSHHDVu><HHDVu><THHDVu>Ống dẫn khí PA 4x6mm</THHDVu><SLuong>1</SLuong><DGia>648148</DGia><ThTien>648148</ThTien><TSuat>8%</TSuat></HHDVu></DSHHDVu>
<TToan><TgTCThue>648148</TgTCThue><TgTThue>51852</TgTThue><TgTTTBSo>{tong}</TgTTTBSo></TToan></NDHDon></DLHDon></HDon>"""
PDF = b"%PDF-1.4\n%fake hoa don\n" + b"0" * 300
LINK_MISA = "https://www.meinvoice.vn/tra-cuu"
LINK_EI = "http://0315297971hd.easyinvoice.com.vn/Invoice/ViewFromEmail?token=TOKENTRONGTHU123"
TRANG_EI = ("<!DOCTYPE html><html><body>HÓA ĐƠN <button onclick=\"downloadPdfAndFileAttachFromAvailableHtml('TOKNUT/abc+def==',1)\">Tải PDF</button>"
            "<button onclick=\"downloadXML('TOKNUT/abc+def==')\">Tải tệp XML</button>"
            "<a href='/Files/UltraViewer_Setup_Guide.pdf'>Hướng dẫn UltraViewer</a></body></html>").encode("utf-8")


def _xml(so="15854", mst="0315341839", tong="700000"):
    return XML.format(so=so, mst=mst, tong=tong).encode("utf-8")


class _Misa:
    """Cổng MISA giả: mã đúng → JSON có XML; mã khác → INVOICENOTEXIST."""

    def __init__(self, ma="7NFQCZ6BA6XV", xml=None, tra=None):
        self.ma, self.xml, self.tra, self.goi_ds = ma, xml or _xml(), tra, []

    def goi(self, url, du_lieu=None):
        self.goi_ds.append((url, du_lieu))
        assert url == "https://www.meinvoice.vn/tra-cuu/GetInvoiceDataByTransactionID" and du_lieu["isReceiveEmail"] == "false"
        if self.tra is not None:
            return self.tra, "text/html", url
        if du_lieu["transactionID"] == self.ma:
            j = {"success": True, "errorCode": None, "data": self.xml.decode("utf-8"), "customData": "x"}
        else:
            j = {"success": False, "errorCode": "INVOICENOTEXIST", "data": None, "customData": 1}
        return json.dumps(j).encode("utf-8"), "application/json; charset=utf-8", url


class _Ei:
    """Cổng EasyInvoice giả theo đúng trình tự thật: trang hóa đơn → DownloadXML (JSON fileGuid) → Download; DownloadPdf."""

    def __init__(self, trang=TRANG_EI, xml=None, pdf=PDF):
        self.trang, self.xml, self.pdf, self.goi_ds = trang, xml or _xml(so="444", mst="0315297971", tong="1425600"), pdf, []

    def goi(self, url, du_lieu=None):
        self.goi_ds.append((url, du_lieu))
        u = urllib.parse.urlsplit(url)
        assert u.hostname == "0315297971hd.easyinvoice.com.vn"
        if u.path == "/Invoice/ViewFromEmail":
            return self.trang, "text/html", url.replace("http://", "https://")       # cổng chuyển sang https
        if u.path == "/Invoice/DownloadXML":
            assert du_lieu == {"token": "TOKNUT/abc+def=="} and url.startswith("https://")
            return json.dumps({"fileGuid": "g-1", "fileName": "444.xml"}).encode(), "application/json", url
        if u.path == "/Invoice/Download":
            assert urllib.parse.parse_qs(u.query) == {"fileGuid": ["g-1"], "fileName": ["444.xml"]}
            return self.xml, "application/octet-stream", url
        if u.path == "/Invoice/DownloadPdf":
            assert urllib.parse.parse_qs(u.query) == {"token": ["TOKNUT/abc+def=="]}
            return self.pdf, "application/pdf", url
        if u.path == "/tai-pdf":
            return self.pdf, "application/pdf", url
        raise AssertionError("gọi lệnh lạ: " + url)


# ---------------------------------------------------------------- module tải ----------------------------------------------------------------
def test_chi_cong_da_kiem_chung_duoc_goi():
    assert tv.kiem_url("https://www.meinvoice.vn/tra-cuu/?sc=ABC") is None
    assert tv.kiem_url("http://3703058418hd.easyinvoice.com.vn/tra-cuu?ma=X") is None
    for xau in ("https://evil.example.com/meinvoice.vn/x", "https://meinvoice.vn.evil.com/x", "ftp://www.meinvoice.vn/x",
                "https://www.meinvoice.vn:8443/x", "https://user:pw@www.meinvoice.vn/x", "http://127.0.0.1/x",
                "http://169.254.169.254/latest/meta-data", "file:///etc/passwd", "", "https://vinvoice.viettel.vn/utilities/invoice-search",
                "http://tracuuhoadon.minvoice.vn/", "http://ehoadon.vn/hdpb6a"):
        assert tv.kiem_url(xau) is not None, xau


def test_nhan_ra_cong_ho_tro():
    c = tv.cong_ho_tro
    assert c(LINK_MISA, "7NFQCZ6BA6XV") == "MISA"                                       # link trang tra cứu + mã trong thư
    assert c("https://www.meinvoice.vn/tra-cuu/?sc=8BFNHK8Q9ZVD&m=a@b.vn&n=CÔNG TY A") == "MISA"   # mã nằm trong link
    assert c(None, "BDF_CZLDPQ8V", "no-reply@meinvoice.vn") == "MISA"                   # thư MISA chỉ có mã
    assert c(LINK_MISA, None) is None and c(None, "BDF_CZLDPQ8V", "ketoan@ncc.vn") is None
    assert c(LINK_EI) == "EASYINVOICE" and c("http://3703058418hd.easyinvoice.com.vn/tra-cuu?ma=7UT2SH9WV") == "EASYINVOICE"
    assert c("https://easyinvoice.vn/") is None
    for khac in ("https://vinvoice.viettel.vn/utilities/invoice-search", "http://tracuuhoadon.minvoice.vn/", "http://ehoadon.vn/hdpb6a",
                 "https://tracuuhoadon.ipos.vn/Invoice/getinvoice?token=x", "https://www.linkedin.com/company/x"):
        assert c(khac, "MA123456") is None, khac
    # link bị Gmail bọc chuyển hướng
    boc = "https://www.google.com/url?q=" + urllib.parse.quote("https://www.meinvoice.vn/tra-cuu/?sc=8BFNHK8Q9ZVD", safe="") + "&source=gmail"
    assert tv.go_boc(boc) == "https://www.meinvoice.vn/tra-cuu/?sc=8BFNHK8Q9ZVD" and c(boc) == "MISA"


def test_misa_tai_xml_theo_ma():
    p = _Misa()
    k = tv.tai_hoa_don(LINK_MISA, "7NFQCZ6BA6XV", phien=p)
    assert k["ok"] and k["cong"] == "MISA" and [t["loai"] for t in k["tep"]] == ["xml"] and k["tep"][0]["data"] == _xml()
    assert len(p.goi_ds) == 1 and p.goi_ds[0][1]["transactionID"] == "7NFQCZ6BA6XV"         # đúng MỘT lệnh, không gọi link khác
    # mã lấy từ sc= trong link (giữ nguyên hoa/thường), kể cả link có ký tự có dấu
    p2 = _Misa(ma="aB9_xYz12345")
    assert tv.tai_hoa_don("https://www.meinvoice.vn/tra-cuu/?sc=aB9_xYz12345&n=CÔNG TY Ô", None, phien=p2)["ok"]
    k3 = tv.tai_hoa_don(LINK_MISA, "MASAI0000000", phien=_Misa())
    assert not k3["ok"] and k3["ho_tro"] and "không có hóa đơn" in k3["ly_do"]
    k4 = tv.tai_hoa_don(LINK_MISA, "7NFQCZ6BA6XV", phien=_Misa(tra=b"<html><body>Access denied</body></html>"))
    assert not k4["ok"] and "không đúng dạng" in k4["ly_do"]


def test_easyinvoice_theo_link_trong_thu_khong_nhan_nham_file_huong_dan():
    p = _Ei()
    k = tv.tai_hoa_don(LINK_EI, "MAKHAC", phien=p)
    assert k["ok"] and k["cong"] == "EASYINVOICE" and [t["loai"] for t in k["tep"]] == ["xml", "pdf"]
    duong = [urllib.parse.urlsplit(u).path for u, _ in p.goi_ds]
    assert duong == ["/Invoice/ViewFromEmail", "/Invoice/DownloadXML", "/Invoice/Download", "/Invoice/DownloadPdf"]
    assert not any("UltraViewer" in u for u, _ in p.goi_ds)                                # KHÔNG dò link chung trong trang
    # trang không có nút tải (link hết hạn) → không tải gì, nêu lý do
    k2 = tv.tai_hoa_don(LINK_EI, phien=_Ei(trang=b"<html><body>Loi<a href='/Files/UltraViewer_Setup_Guide.pdf'>x</a></body></html>"))
    assert not k2["ok"] and "không có nút tải" in k2["ly_do"]
    # DownloadPdf trả trang lỗi (HTML) → chỉ nhận XML
    k3 = tv.tai_hoa_don(LINK_EI, phien=_Ei(pdf=b"<html><body>error</body></html>"))
    assert k3["ok"] and [t["loai"] for t in k3["tep"]] == ["xml"]
    # thư kiểu cũ: /tra-cuu?ma= → tải nhanh PDF /tai-pdf?ma=
    p4 = _Ei()
    k4 = tv.tai_hoa_don("http://0315297971hd.easyinvoice.com.vn/tra-cuu?ma=7UT2SH9WV", phien=p4)
    assert k4["ok"] and [t["loai"] for t in k4["tep"]] == ["pdf"] and p4.goi_ds[0][0].endswith("/tai-pdf?ma=7UT2SH9WV")


def test_cong_chua_ho_tro_khong_goi_mang():
    class _Cam:
        def goi(self, url, du_lieu=None):
            raise AssertionError("không được gọi mạng: " + url)
    for link in ("https://vinvoice.viettel.vn/utilities/invoice-search", "http://tracuuhoadon.minvoice.vn/", "https://hoadon.cong-la.vn/x?ma=1"):
        k = tv.tai_hoa_don(link, "MA123456", phien=_Cam())
        assert not k["ok"] and k["ho_tro"] is False and "chưa hỗ trợ tự tải" in k["ly_do"]
    k2 = tv.tai_hoa_don(None, "MA123456", "ketoan@ncc.vn", phien=_Cam())
    assert not k2["ok"] and k2["ho_tro"] is False


def test_nhan_dang_va_goi_zip():
    assert tv.nhan_dang(PDF) == "pdf" and tv.nhan_dang(_xml()) == "xml" and tv.nhan_dang(TRANG_EI) == "html"
    assert tv.nhan_dang(b"") is None and tv.nhan_dang(b"khong phai file") is None
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("hoadon.pdf", PDF)
        z.writestr("hoadon.xml", _xml())
    assert tv.nhan_dang(b.getvalue()) == "zip" and sorted(x[0] for x in tv.tu_zip(b.getvalue())) == ["pdf", "xml"]


def test_chuyen_huong_ra_ngoai_bi_chan():
    import urllib.error

    class _Mo:
        def open(self, req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 302, "Found", {"Location": "http://169.254.169.254/latest"}, None)
    p = tv.Phien()
    p._mo = _Mo()
    with pytest.raises(ValueError) as e:                       # conftest thay Phien.goi bằng bản «tắt mạng», bản thật ở _goi_goc
        tv.Phien._goi_goc(p, "https://www.meinvoice.vn/tra-cuu/GetInvoiceDataByTransactionID", {"transactionID": "A"})
    assert "chưa hỗ trợ tự tải" in str(e.value)


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
        c.exec_driver_sql("INSERT INTO nha_cung_cap (id, ten, ma_so_thue) VALUES (7, 'NINOL', '0315341839')")
    return sessionmaker(eng)()


def _dong(s, id_=1, tong=0, so="00015854", **kw):
    r = m.KtHoaDonCho(id=id_, tu_email="ketoan@ninol.com", so_hoa_don=so, tong_tien=tong, tien_truoc_thue=0, thue_suat=8,
                      trang_thai="CHO_XAC_NHAN", link_tra_cuu=LINK_MISA, ma_tra_cuu="7NFQCZ6BA6XV", nguon_doc="AI", tai_lan=0, **kw)
    s.add(r); s.commit()
    return r


def test_dong_0_dong_duoc_dien_tien_tu_xml_misa_va_luu_file(db):
    r = _dong(db)
    assert kq._hdc_cong_tai(r) == "MISA" and kq._hdc_can_tu_tai(r) is True
    k = kq._hdc_tu_tai(db, r, None, phien=_Misa())
    db.commit()
    assert k["ok"] and k["dien_tien"] and k["nguon"] == "XML" and k["cong"] == "MISA"
    assert (int(r.tong_tien), int(r.tien_truoc_thue), int(r.thue_suat)) == (700000, 648148, 8)
    assert r.ngay_hd == date(2026, 10, 31) and r.ky_hieu == "1C26TYY" and r.ncc_mst == "0315341839" and r.nha_cung_cap_id == 7
    assert r.nguon_doc == "XML" and r.tai_tt == "OK" and r.tai_lan == 1 and r.mo_ta.startswith("📄 tiền theo file XML")
    assert r.tai_ghi_chu == "Đã tải XML từ MISA meInvoice"
    tep = kq._hdc_tep(db, [r.id])[r.id]
    assert [t["loai"] for t in tep] == ["HDDT_XML"] and tep[0]["ten_file"] == "HD_00015854_1C26TYY.xml"
    assert open(db.get(m.TepDinhKem, tep[0]["id"]).duong_dan, "rb").read() == _xml()
    assert kq._hdc_can_tu_tai(r) is False                       # đã có file → không tải lại tự động
    assert db.query(m.AuditLog).filter_by(hanh_dong="TU_TAI_HDC").count() == 1


def test_khong_ghi_de_tien_hop_le_chi_canh_bao(db):
    r = _dong(db, tong=999_000)
    r.tien_truoc_thue = 925_000
    db.commit()
    k = kq._hdc_tu_tai(db, r, None, phien=_Misa())
    assert k["ok"] and not k["dien_tien"] and "chưa đổi" in k["canh_bao"] and int(r.tong_tien) == 999_000
    assert r.tai_tt == "OK" and "⚠" in r.tai_ghi_chu


def test_vat_uoc_duoc_thay_bang_so_that_khi_tong_khop(db):
    r = _dong(db, tong=700_000, mo_ta="⚠ VAT ước 8% từ tổng — kiểm tra lại · ống khí")
    r.tien_truoc_thue = 648_200
    db.commit()
    kq._hdc_tu_tai(db, r, None, phien=_Misa())
    assert int(r.tien_truoc_thue) == 648_148 and "VAT ước" not in r.mo_ta and r.mo_ta.startswith("📄 VAT theo file XML")


def test_file_la_hoa_don_so_khac_thi_khong_dung(db):
    r = _dong(db, so="999")
    k = kq._hdc_tu_tai(db, r, None, phien=_Misa())
    assert not k["ok"] and "hóa đơn số 15854" in k["ly_do"] and int(r.tong_tien) == 0
    assert r.tai_tt == "LOI" and kq._hdc_tep(db, [r.id]) == {}
    r2 = _dong(db, id_=2, so="15854", ncc_mst="0101010101")            # cùng số nhưng bên bán khác MST
    k2 = kq._hdc_tu_tai(db, r2, None, phien=_Misa())
    assert not k2["ok"] and "MST 0315341839" in k2["ly_do"]


def test_chay_thu_khong_ghi_gi(db):
    r = _dong(db)
    k = kq._hdc_tu_tai(db, r, None, thu=True, phien=_Misa())
    assert k["ok"] and k["doc"]["so_tien"] == 700000.0 and k["tep"][0]["loai"] == "xml"
    assert int(r.tong_tien) == 0 and r.tai_tt is None and (r.tai_lan or 0) == 0 and kq._hdc_tep(db, [r.id]) == {}


def test_cong_chua_ho_tro_khong_duoc_xep_hang_va_gioi_han_so_lan(db):
    r = _dong(db)
    r.link_tra_cuu, r.ma_tra_cuu = "https://vinvoice.viettel.vn/utilities/invoice-search", None
    db.commit()
    assert kq._hdc_cong_tai(r) is None and kq._hdc_can_tu_tai(r) is False            # không vào hàng tự tải, không gọi mạng
    k = kq._hdc_tu_tai(db, r, None)                                                # bấm tay vẫn trả lý do rõ
    assert not k["ok"] and r.tai_tt == "KHONG_HT" and "chưa hỗ trợ tự tải" in r.tai_ghi_chu
    r2 = _dong(db, id_=2)
    for _ in range(3):
        assert kq._hdc_can_tu_tai(r2) is True
        kq._hdc_tu_tai(db, r2, None, phien=_Misa(ma="MAKHAC"))                     # cổng báo không có hóa đơn
    assert r2.tai_tt == "LOI" and r2.tai_lan == 3 and kq._hdc_can_tu_tai(r2) is False and "không có hóa đơn" in r2.tai_ghi_chu


def test_easyinvoice_dien_dong_va_luu_ca_xml_pdf(db):
    r = _dong(db, so="444")
    r.link_tra_cuu, r.ma_tra_cuu, r.tu_email = LINK_EI, None, "hoadon-noreply@easyinvoice.vn"
    db.commit()
    k = kq._hdc_tu_tai(db, r, None, phien=_Ei())
    assert k["ok"] and k["nguon"] == "XML" and int(r.tong_tien) == 1425600 and r.tai_ghi_chu == "Đã tải XML + PDF từ EasyInvoice"
    assert [t["loai"] for t in kq._hdc_tep(db, [r.id])[r.id]] == ["HDDT_XML", "HDDT_PDF"]


def test_chi_co_pdf_thi_nho_ai_khi_dong_con_thieu(db, monkeypatch):
    import app.ai_gateway as ag
    goi = []
    monkeypatch.setattr(ag, "doc_hoa_don_tep", lambda d, ct, fn, goi_y=None: (goi.append(fn) or
                        {"so_hoa_don": "444", "so_tien": 1425600, "tien_truoc_thue": 1320000, "tien_thue": 105600, "ngay": "2026-11-16"}))
    cu = "http://0315297971hd.easyinvoice.com.vn/tra-cuu?ma=7UT2SH9WV"
    r = _dong(db, so="444")
    r.link_tra_cuu = cu
    db.commit()
    k = kq._hdc_tu_tai(db, r, None, phien=_Ei())
    assert k["ok"] and k["nguon"] == "PDF" and int(r.tong_tien) == 1425600 and r.nguon_doc == "PDF" and goi == ["hoa_don.pdf"]
    r2 = _dong(db, id_=2, so="444", tong=1_425_600, ngay_hd=date(2026, 11, 16))    # dòng đã đủ số liệu → chỉ lưu PDF, không tốn AI
    r2.link_tra_cuu = cu
    db.commit()
    k2 = kq._hdc_tu_tai(db, r2, None, phien=_Ei())
    assert k2["ok"] and k2["nguon"] is None and len(goi) == 1 and kq._hdc_tep(db, [2])[2][0]["loai"] == "HDDT_PDF"


class _Nd:
    id = None


def test_endpoint_mot_dong_va_hang_loat(db, monkeypatch):
    gia = _Misa()
    monkeypatch.setattr(tv.Phien, "goi", lambda self, url, du_lieu=None: gia.goi(url, du_lieu))
    monkeypatch.setattr("time.sleep", lambda s: None)
    _dong(db, id_=1)                               # thiếu tiền → làm trước
    _dong(db, id_=2, tong=700_000)
    r3 = _dong(db, id_=3)
    r3.link_tra_cuu = r3.ma_tra_cuu = None
    r4 = _dong(db, id_=4)                          # cổng chưa hỗ trợ → không vào lượt hàng loạt
    r4.link_tra_cuu, r4.ma_tra_cuu = "http://tracuuhoadon.minvoice.vn/", "MINV12345"
    db.commit()
    with pytest.raises(HTTPException) as e:
        kq.tu_tai_hoa_don_cho(3, False, db, _Nd())
    assert e.value.status_code == 400
    thu = kq.tu_tai_hoa_don_cho(1, True, db, _Nd())
    assert thu["ok"] and thu["tong_tien"] == 0
    loat = kq.tu_tai_hoa_don_cho_loat(10, db, _Nd())
    assert (loat["da_xet"], loat["tai_duoc"], loat["dien_tien"], loat["con_lai"]) == (2, 2, 1, 0)
    assert loat["chi_tiet"][0]["id"] == 1 and r4.tai_tt is None
    assert kq.tu_tai_hoa_don_cho_loat(10, db, _Nd())["da_xet"] == 0          # đã có file → không tải lại
    tep = kq._hdc_tep(db, [1, 2, 3, 4])
    assert sorted(tep) == [1, 2] and len(tep[1]) == 1
    assert kq.tai_tep_hoa_don_cho(tep[1][0]["id"], db, None) is not None      # mở lại được file đã tải


XML_MISA_RIENG = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<inv:invoice xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1" xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
<inv:invoiceData id="data"><inv:invoiceType>01GTKT</inv:invoiceType><inv:templateCode>1</inv:templateCode>
<inv:invoiceSeries>1C26TAP</inv:invoiceSeries><inv:invoiceIssuedDate>2026-10-31T00:00:00</inv:invoiceIssuedDate>
<inv:sellerLegalName>CÔNG TY CỔ PHẦN HÓA CHẤT VÀ MÔI TRƯỜNG AN PHÚ</inv:sellerLegalName><inv:sellerTaxCode>0314515377</inv:sellerTaxCode>
<inv:buyerLegalName>CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT</inv:buyerLegalName><inv:buyerTaxCode>0303620066</inv:buyerTaxCode>
<inv:items><inv:item><inv:itemName>Poly aluminium chloride (PAC) 10%</inv:itemName><inv:vatPercentage>8</inv:vatPercentage></inv:item></inv:items>
<inv:totalAmountWithoutVAT>50013000 </inv:totalAmountWithoutVAT><inv:totalVATAmount>4001040 </inv:totalVATAmount>
<inv:totalAmountWithVAT>54014040 </inv:totalAmountWithVAT><inv:invoiceNumber>00005523</inv:invoiceNumber></inv:invoiceData></inv:invoice>"""


def test_doc_ca_hai_dang_xml(db):
    a = tv.doc_xml_hoa_don(_xml())
    assert (a["so_hoa_don"], a["ky_hieu"], a["ngay"], a["so_tien"], a["ncc_mst"]) == ("15854", "1C26TYY", "2026-10-31", 700000.0, "0315341839")
    b = tv.doc_xml_hoa_don(XML_MISA_RIENG.encode("utf-8"))                       # dạng riêng của MISA (<inv:invoice>)
    assert (b["so_hoa_don"], b["ky_hieu"], b["ngay"]) == ("5523", "1C26TAP", "2026-10-31")
    assert (b["so_tien"], b["tien_truoc_thue"], b["tien_thue"], b["ncc_mst"]) == (54014040.0, 50013000.0, 4001040.0, "0314515377")
    assert b["ncc_ten"].endswith("AN PHÚ") and b["mo_ta"].startswith("Poly aluminium")
    assert tv.doc_xml_hoa_don(b"<a><b>khong phai hoa don</b></a>") is None
    with pytest.raises(ValueError):
        tv.doc_xml_hoa_don(b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e "x">]><HDon><SHDon>&e;</SHDon></HDon>')
    # dòng hàng chờ nhận số liệu từ dạng riêng của MISA
    r = _dong(db, so="00005523")
    r.ma_tra_cuu = "BDF_CZLDPQ8V"
    db.commit()
    k = kq._hdc_tu_tai(db, r, None, phien=_Misa(ma="BDF_CZLDPQ8V", xml=XML_MISA_RIENG.encode("utf-8")))
    assert k["ok"] and k["nguon"] == "XML" and (int(r.tong_tien), int(r.tien_truoc_thue), int(r.thue_suat)) == (54014040, 50013000, 8)
    assert r.ky_hieu == "1C26TAP" and r.ncc_mst == "0314515377" and r.ngay_hd == date(2026, 10, 31)


def test_easyinvoice_trang_ma_hoa_dau_nhay_va_so_hoa_don_rac(db):
    # HTML thô của cổng ghi onclick="downloadXML(&#39;token&#39;)" — dấu nháy bị mã hóa thành thực thể
    tho = TRANG_EI.decode("utf-8").replace("'", "&#39;").encode("utf-8")
    assert b"downloadXML(&#39;" in tho
    k = tv.tai_hoa_don(LINK_EI, phien=_Ei(trang=tho))
    assert k["ok"] and [t["loai"] for t in k["tep"]] == ["xml", "pdf"]
    # dòng có «số hóa đơn» không chứa chữ số (AI đọc nhầm chữ «Invoice») → coi như chưa có số, nhận số từ file
    r = _dong(db, so="oice", tong=3465)
    k2 = kq._hdc_tu_tai(db, r, None, phien=_Misa())
    assert k2["ok"] and r.so_hoa_don == "15854" and "chưa đổi" in k2["canh_bao"] and int(r.tong_tien) == 3465
    assert kq._hdc_tep(db, [r.id])[r.id][0]["ten_file"] == "HD_15854_1C26TYY.xml"
