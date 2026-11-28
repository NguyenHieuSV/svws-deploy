"""⬇ TỰ TẢI HÓA ĐƠN từ LINK / MÃ TRA CỨU trong thư cổng hóa đơn điện tử (anh Hiếu 26/11/2026; viết lại 27/11/2026).

Thư cổng HĐĐT thường KHÔNG đính kèm file: chỉ có link tra cứu + mã. Module này tải thẳng file hóa đơn để app đọc số tiền
chính xác và lưu file kèm dòng hàng chờ — kế toán khỏi mở link, dán mã.

CHỈ tải ở cổng ĐÃ KIỂM CHỨNG cách tải với hóa đơn thật (27/11/2026) — KHÔNG dò link chung trong trang web
(bản đầu dò link có chữ «pdf» đã nhận nhầm file hướng dẫn phần mềm của cổng là hóa đơn):
  • MISA meInvoice — theo MÃ TRA CỨU: POST tra-cuu/GetInvoiceDataByTransactionID → JSON, trường `data` là nguyên XML hóa đơn
    (chính lệnh trang tra cứu gọi khi mở link «?sc=<mã>» trong thư; không cần mã xác minh hình ảnh).
  • EasyInvoice (Softdreams) — theo LINK trong thư «…/Invoice/ViewFromEmail?token=…»: lấy mã tải trong trang hóa đơn rồi
    làm như nút «Tải tệp XML» (POST /Invoice/DownloadXML → fileGuid → GET /Invoice/Download, giữ cookie phiên);
    thư kiểu cũ có sẵn link «…/tai-pdf?ma=<mã>».
Cổng khác (Viettel, VNPT, M-Invoice, BKAV… đòi mã xác minh hình ảnh / đăng nhập) → «chưa hỗ trợ», không gọi mạng.

AN TOÀN (link nằm trong thư = dữ liệu KHÔNG tin cậy):
  • chỉ gọi tới tên miền trong `MIEN_CHO_PHEP`, kiểm ở MỌI chặng chuyển hướng; chỉ http/https cổng mặc định;
  • mỗi lần gọi ≤ `TIMEOUT` giây, mỗi file ≤ `GIOI_HAN` (8 MB), cả hóa đơn ≤ `han_s` giây;
  • nhận dạng file theo CHỮ KÝ ĐẦU FILE (PDF / XML / ZIP), không tin Content-Type.
Không ghi CSDL, không gọi AI ở đây — nơi gọi (`ke_toan_quy._hdc_tu_tai`) đọc file, đối chiếu số hóa đơn và điền dòng.
"""
import html
import http.cookiejar
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

GIOI_HAN = 8 * 1024 * 1024          # 8 MB / file
TIMEOUT = 20                        # giây / lần gọi
SO_CHUYEN_HUONG = 4
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# Tên miền được phép gọi (khớp đúng tên hoặc tên miền con) — CHỈ cổng đã có cách tải kiểm chứng ở dưới.
MIEN_CHO_PHEP = (
    "meinvoice.vn",                              # MISA meInvoice
    "easyinvoice.com.vn", "easyinvoice.vn",      # EasyInvoice (Softdreams): <MST>hd.easyinvoice.com.vn
)
_MISA_API = "https://www.meinvoice.vn/tra-cuu/GetInvoiceDataByTransactionID"
_THAM_SO_MA = ("sc", "code", "ma", "matracuu", "ma_tra_cuu")


def thuoc_cong(host: str, mien=None) -> bool:
    host = (host or "").strip(".").lower()
    for d in ([mien] if mien else MIEN_CHO_PHEP):
        if host == d or host.endswith("." + d):
            return True
    return False


def _sach(url: str) -> str:
    """URL chỉ còn ký tự ASCII (link trong thư có khi chứa tên công ty có dấu ở tham số) — không mã hóa lại dấu %."""
    return urllib.parse.quote(url or "", safe="!#$%&'()*+,/:;=?@[]~")


def kiem_url(url: str) -> str | None:
    """URL hợp lệ để gọi → None; không hợp lệ → lý do. Chỉ http/https, cổng mặc định, tên miền cổng HĐĐT được phép."""
    try:
        u = urllib.parse.urlsplit(url or "")
    except ValueError:
        return "link hỏng"
    if u.scheme not in ("http", "https"):
        return "link không phải http/https"
    if u.username or u.password:
        return "link có tài khoản nhúng"
    try:
        cong = u.port
    except ValueError:
        return "link hỏng"
    if cong not in (None, 80, 443):
        return "link dùng cổng lạ"
    if not thuoc_cong(u.hostname or ""):
        return f"cổng {(u.hostname or '?')[:60]} chưa hỗ trợ tự tải"
    return None


def go_boc(link: str | None) -> str:
    """Bỏ lớp bọc chuyển hướng của Gmail («https://www.google.com/url?q=<link thật>&…») để lấy link thật."""
    link = (link or "").strip()
    try:
        u = urllib.parse.urlsplit(link)
    except ValueError:
        return link
    if (u.hostname or "").lower() in ("www.google.com", "google.com") and u.path == "/url":
        q = urllib.parse.parse_qs(u.query).get("q") or urllib.parse.parse_qs(u.query).get("url")
        if q and q[0].startswith(("http://", "https://")):
            return q[0]
    return link


def ma_tu_link(link: str) -> str | None:
    """Mã tra cứu nằm trong tham số của link (sc= / ma= / code= …), giữ nguyên chữ hoa/thường."""
    try:
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(link or "").query, keep_blank_values=False)
    except ValueError:
        return None
    thap = {k.lower(): v[0] for k, v in q.items() if v and v[0]}
    for k in _THAM_SO_MA:
        if thap.get(k):
            return thap[k].strip()[:60]
    return None


def cong_ho_tro(link: str | None, ma: str | None = None, tu_email: str | None = None) -> str | None:
    """Cổng app tự tải được cho link / mã này: 'MISA' · 'EASYINVOICE' · None (chưa hỗ trợ). Không gọi mạng."""
    link = go_boc(link)
    try:
        host = (urllib.parse.urlsplit(link).hostname or "").lower() if link else ""
    except ValueError:
        host = ""
    mien_gui = (tu_email or "").split("@")[-1].strip().lower()
    code = (ma_tu_link(link) if link else None) or (ma or "").strip()
    if thuoc_cong(host, "meinvoice.vn") or (not host and ("meinvoice" in mien_gui or "misa" in mien_gui)):
        return "MISA" if re.fullmatch(r"[A-Za-z0-9_\-]{6,40}", code or "") else None
    if thuoc_cong(host, "easyinvoice.com.vn") or thuoc_cong(host, "easyinvoice.vn"):
        try:
            duong = urllib.parse.urlsplit(link).path.lower()
        except ValueError:
            return None
        if "/invoice/viewfromemail" in duong or (code and "tra-cuu" in duong) or "tai-pdf" in duong:
            return "EASYINVOICE"
    return None


class TamNgung(ValueError):
    """Cổng TẠM THỜI không phục vụ — giới hạn số lần gọi (HTTP 429) hoặc cổng đang nghẽn (502 / 503 / 504). Không phải lỗi của
    hóa đơn → nơi gọi KHÔNG tính là một lần thử hỏng, ngưng gọi cổng đó một lúc rồi thử lại. `cho_s`: số giây cổng đề nghị chờ.
    (28/11/2026: chạy hàng loạt ~40 lệnh liền nhau thì MISA trả 429; các dòng sau bị ghi «lỗi» oan và hết 3 lượt thử.)"""

    def __init__(self, ly_do: str, cho_s: int | None = None):
        super().__init__(ly_do)
        self.cho_s = cho_s


_MA_TAM_NGUNG = (429, 502, 503, 504)


def _cho_s(v) -> int | None:
    """Đầu mục Retry-After dạng số giây → int trong 1…3600; dạng khác (ngày giờ) / trống → None."""
    try:
        s = int(str(v or "").strip())
    except ValueError:
        return None
    return s if 0 < s <= 3600 else None


class _KhongChuyenHuong(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):      # tự xử lý chuyển hướng để kiểm từng chặng
        return None


class Phien:
    """Một phiên HTTP giữ cookie cho MỘT hóa đơn (cổng cần cookie giữa các bước). Test thay bằng đối tượng giả có `.goi`."""

    def __init__(self):
        self._mo = urllib.request.build_opener(_KhongChuyenHuong,
                                               urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def goi(self, url: str, du_lieu: dict | None = None) -> tuple[bytes, str, str]:
        """GET, hoặc POST dạng form khi có `du_lieu`. Tự theo chuyển hướng ≤ SO_CHUYEN_HUONG chặng (mỗi chặng phải thuộc
        cổng được phép; sau chuyển hướng luôn là GET). → (dữ liệu ≤ GIOI_HAN, content-type, url cuối). Lỗi → ValueError."""
        than = urllib.parse.urlencode(du_lieu).encode("utf-8") if du_lieu is not None else None
        url = _sach(url)
        for _ in range(SO_CHUYEN_HUONG + 1):
            ly = kiem_url(url)
            if ly:
                raise ValueError(ly)
            dau = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "vi,en;q=0.8"}
            if than is not None:
                dau["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                dau["X-Requested-With"] = "XMLHttpRequest"
            req = urllib.request.Request(url, data=than, headers=dau)
            try:
                with self._mo.open(req, timeout=TIMEOUT) as r:
                    data = r.read(GIOI_HAN + 1)
                    if len(data) > GIOI_HAN:
                        raise ValueError("file lớn hơn 8 MB")
                    return data, (r.headers.get("Content-Type") or ""), url
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
                    url, than = _sach(urllib.parse.urljoin(url, e.headers["Location"])), None
                    continue
                if e.code in _MA_TAM_NGUNG:
                    raise TamNgung(("cổng đang giới hạn số lần gọi" if e.code == 429 else "cổng đang nghẽn")
                                   + f" (HTTP {e.code})", _cho_s(e.headers.get("Retry-After") if e.headers else None))
                raise ValueError(f"cổng trả lỗi HTTP {e.code}")
            except urllib.error.URLError as e:
                raise ValueError(f"không kết nối được cổng ({str(getattr(e, 'reason', e))[:60]})")
            except (TimeoutError, OSError) as e:
                raise ValueError(f"cổng không trả lời ({type(e).__name__})")
        raise ValueError("chuyển hướng quá nhiều lần")


def nhan_dang(data: bytes) -> str | None:
    """Loại file theo chữ ký đầu file: 'zip' · 'xml' · 'html' · 'pdf' · None (rỗng / lạ)."""
    if not data:
        return None
    dau = data[:2048]
    if dau.startswith(b"PK\x03\x04"):                # gói ZIP — xét trước: ZIP không nén chứa nguyên chữ «%PDF-» của file bên trong
        return "zip"
    t = dau.lstrip(b"\xef\xbb\xbf \r\n\t").lower()
    if t.startswith(b"<"):
        if t.startswith(b"<!doctype html") or b"<html" in t or b"<head" in t or b"<body" in t:
            return "html"
        return "xml"
    if b"%PDF-" in dau[:1024]:
        return "pdf"
    return None


def tu_zip(data: bytes) -> list[tuple[str, bytes]]:
    """File XML / PDF đầu tiên trong gói ZIP (mỗi loại một file, ≤ GIOI_HAN sau giải nén) → [(loại, dữ liệu)]."""
    ra, co = [], set()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for i in z.infolist()[:40]:
                ten = i.filename.lower()
                loai = "xml" if ten.endswith(".xml") else "pdf" if ten.endswith(".pdf") else None
                if not loai or loai in co or i.is_dir() or i.file_size > GIOI_HAN:
                    continue
                d = z.read(i)
                if nhan_dang(d) == loai:
                    co.add(loai)
                    ra.append((loai, d))
    except (zipfile.BadZipFile, RuntimeError, OSError):
        return []
    return ra


def _so_f(x) -> float:
    try:
        return float(str(x if x is not None else 0).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def doc_xml_hoa_don(data: bytes) -> dict | None:
    """XML hóa đơn → {ncc_ten, ncc_mst, nguoi_mua, nguoi_mua_mst, so_hoa_don, ky_hieu, ngay, so_tien, tien_truoc_thue,
    tien_thue, mo_ta}; không phải hóa đơn → None; XML hỏng / có DTD → ValueError. Đọc thẳng theo thẻ, không AI. Hai dạng:
      • chuẩn cơ quan thuế TT78 / NĐ123 (<HDon>… SHDon, TgTTTBSo) — dùng lại hoa_don_ban_doc.doc_xml;
      • dạng riêng của MISA (<inv:invoice>… invoiceNumber, totalAmountWithVAT) — cổng MISA trả dạng này cho một số bên bán."""
    import xml.etree.ElementTree as ET
    from .hoa_don_ban_doc import doc_xml
    x = doc_xml(data)                                   # tự chặn DTD / ENTITY và báo ValueError khi XML hỏng
    if x:
        return {"ncc_ten": x.get("ten_nguoi_ban"), "ncc_mst": (x.get("mst_nguoi_ban") or "").replace("-", "").strip() or None,
                "nguoi_mua": x.get("ten_nguoi_mua"), "nguoi_mua_mst": (x.get("mst_nguoi_mua") or "").replace("-", "").strip() or None,
                "so_hoa_don": x.get("so_hoa_don"), "ky_hieu": (f"{x.get('mau_so') or ''}{x.get('ky_hieu') or ''}".strip() or None),
                "ngay": x.get("ngay"), "so_tien": x.get("so_tien"), "tien_truoc_thue": x.get("tien_truoc_thue"),
                "tien_thue": x.get("tien_thue"), "mo_ta": x.get("mo_ta")}
    goc = ET.fromstring(data)                           # doc_xml ở trên đã kiểm DTD + cú pháp
    the = {}
    hang = []
    for e in goc.iter():
        ten = e.tag.rsplit("}", 1)[-1] if isinstance(e.tag, str) else ""
        gia_tri = (e.text or "").strip()
        if ten == "itemName" and gia_tri:
            hang.append(gia_tri)
        if ten and gia_tri and ten not in the:
            the[ten] = gia_tri
    so = the.get("invoiceNumber")
    if not so:
        return None
    tong, truoc, thue = _so_f(the.get("totalAmountWithVAT")), _so_f(the.get("totalAmountWithoutVAT")), _so_f(the.get("totalVATAmount"))
    if not tong:
        tong = truoc + thue
    if not truoc and tong:
        truoc = tong - thue
    mau, seri = (the.get("templateCode") or "").strip(), (the.get("invoiceSeries") or "").strip()
    ky_hieu = seri if (not mau or seri.startswith(mau)) else mau + seri
    ngay = (the.get("invoiceIssuedDate") or "")[:10]
    return {"ncc_ten": the.get("sellerLegalName"), "ncc_mst": (the.get("sellerTaxCode") or "").replace("-", "").strip() or None,
            "nguoi_mua": the.get("buyerLegalName"), "nguoi_mua_mst": (the.get("buyerTaxCode") or "").replace("-", "").strip() or None,
            "so_hoa_don": so.lstrip("0") or so, "ky_hieu": ky_hieu or None,
            "ngay": ngay if re.fullmatch(r"\d{4}-\d{2}-\d{2}", ngay) else None,
            "so_tien": tong, "tien_truoc_thue": truoc, "tien_thue": thue,
            "mo_ta": " · ".join(hang[:4])[:300] or None}


def _ten(url: str) -> str:
    """Tên ngắn của URL để ghi nhật ký (máy chủ + đường dẫn, không kèm mã / token)."""
    u = urllib.parse.urlsplit(url)
    return f"{u.hostname}{u.path}"[:90]


class _Lan:
    """Gom kết quả một lần tự tải: file nhận được + nhật ký các lệnh đã gọi + hạn thời gian."""

    def __init__(self, phien, han_s):
        self.phien, self.het = phien, time.monotonic() + han_s
        self.tep, self.da_thu, self.ly_do = {}, [], None
        self.tam_ngung, self.cho_s = None, None          # cổng tạm ngưng phục vụ (HTTP 429 …): lý do + số giây nên chờ

    def goi(self, url, du_lieu=None):
        """Gọi một lệnh; lỗi → ghi nhật ký và trả (None, '', url)."""
        if time.monotonic() > self.het:
            self.da_thu.append({"url": _ten(url), "kq": "hết thời gian"})
            return None, "", url
        try:
            data, ct, cuoi = self.phien.goi(url, du_lieu)
        except TamNgung as e:
            self.tam_ngung, self.cho_s = str(e)[:80], e.cho_s
            self.da_thu.append({"url": _ten(url), "kq": "tạm ngưng: " + str(e)[:80]})
            return None, "", url
        except ValueError as e:
            self.da_thu.append({"url": _ten(url), "kq": "lỗi: " + str(e)[:80]})
            return None, "", url
        except Exception as e:                                           # noqa: BLE001 — không để lỗi lạ làm hỏng lượt quét
            self.da_thu.append({"url": _ten(url), "kq": f"lỗi: {type(e).__name__}"})
            return None, "", url
        return data, ct, cuoi

    def nhan(self, data, url, chi=None) -> bool:
        """Nhận file (xml / pdf / zip chứa chúng); `chi` = chỉ nhận loại này. → True khi có thêm file."""
        loai = nhan_dang(data or b"")
        self.da_thu.append({"url": _ten(url), "kq": loai or "rỗng / không nhận ra"})
        cap = tu_zip(data) if loai == "zip" else [(loai, data)] if loai in ("xml", "pdf") else []
        them = False
        for l2, d2 in cap:
            if (chi is None or l2 == chi) and l2 not in self.tep:
                self.tep[l2] = {"loai": l2, "data": d2, "nguon": _ten(url),
                                "content_type": "application/xml" if l2 == "xml" else "application/pdf"}
                them = True
        return them


def _misa(lan: _Lan, code: str):
    """MISA meInvoice: một lệnh POST theo mã tra cứu → JSON {success, errorCode, data: '<HDon>…'}."""
    data, _ct, _u = lan.goi(_MISA_API, {"transactionID": code, "isReceiveEmail": "false"})
    if data is None:
        return
    try:
        j = json.loads(data.decode("utf-8", errors="replace"))
    except ValueError:
        lan.da_thu.append({"url": _ten(_MISA_API), "kq": nhan_dang(data) or "không phải JSON"})
        lan.ly_do = "cổng MISA trả lời không đúng dạng (có thể đang chặn truy cập tự động)"
        return
    xml = j.get("data") if isinstance(j, dict) else None
    if isinstance(j, dict) and j.get("success") and isinstance(xml, str) and xml.lstrip("﻿ \r\n\t").startswith("<"):
        lan.nhan(xml.lstrip("﻿").encode("utf-8"), _MISA_API, chi="xml")
        return
    ma_loi = str((j or {}).get("errorCode") or "") if isinstance(j, dict) else ""
    lan.da_thu.append({"url": _ten(_MISA_API), "kq": "cổng báo: " + (ma_loi or "không có hóa đơn")[:40]})
    lan.ly_do = ("cổng MISA báo mã tra cứu này không có hóa đơn (mã sai hoặc hóa đơn đã bị hủy / thay thế)"
                 if ma_loi.upper() == "INVOICENOTEXIST" else f"cổng MISA không trả hóa đơn ({ma_loi or 'không rõ lý do'})")


# Trang hóa đơn EasyInvoice (kiểm 28/11/2026 với hóa đơn thật): HTML thô KHÔNG có sẵn nút tải — nút do JS dựng từ mã tải
# (128 ký tự, mỗi lần mở trang cấp mã mới) nằm ở đối số cuối của lời gọi nội tuyến «showInv(data.str, …, '<mã tải>');».
_RE_EI_TOK = re.compile(r"showInv\(\s*data\.str[^;]{0,700}?'([A-Za-z0-9+/=]{40,600})'\s*\)\s*;")
_RE_EI_XML = re.compile(r"downloadXML\(\s*'([^']{10,600})'")          # dự phòng: cổng dựng sẵn nút trong HTML


def _easyinvoice(lan: _Lan, link: str, code: str | None):
    """EasyInvoice: link «/Invoice/ViewFromEmail?token=…» → mã tải trong trang → POST /Invoice/DownloadXML (JSON fileGuid)
    → GET /Invoice/Download (cần cookie của phiên — `Phien` giữ). /Invoice/DownloadPdf với mã này KHÔNG trả PDF nên không gọi.
    Thư kiểu cũ «/tra-cuu?ma=<mã>»: chỉ có link tải nhanh PDF «/tai-pdf?ma=<mã>»."""
    u = urllib.parse.urlsplit(link)
    duong = u.path.lower()
    if "/invoice/viewfromemail" in duong:
        data, _ct, cuoi = lan.goi(link)
        if data is None:
            return
        if nhan_dang(data) != "html":
            lan.nhan(data, cuoi)
            return
        lan.da_thu.append({"url": _ten(cuoi), "kq": "trang hóa đơn"})
        # HTML thô ghi onclick="downloadXML(&#39;token&#39;)" (dấu nháy bị mã hóa) → giải mã thực thể trước khi dò
        trang = html.unescape(data[:600000].decode("utf-8", errors="replace"))
        uc = urllib.parse.urlsplit(cuoi)
        goc = f"{uc.scheme}://{uc.netloc}"
        mx = _RE_EI_TOK.search(trang) or _RE_EI_XML.search(trang)
        if not mx:
            lan.ly_do = "trang EasyInvoice không có mã tải (link trong thư đã hết hạn hoặc hóa đơn không còn)"
            return
        d2, _c2, u2 = lan.goi(goc + "/Invoice/DownloadXML", {"token": mx.group(1)})
        if d2 is None:
            return
        try:
            j = json.loads(d2.decode("utf-8", errors="replace"))
        except ValueError:
            j = None
        if not (isinstance(j, dict) and j.get("fileGuid")):
            lan.da_thu.append({"url": _ten(u2), "kq": "cổng báo: " + str((j or {}).get("msg") or "không trả file")[:60]})
            lan.ly_do = "cổng EasyInvoice không cấp file XML cho hóa đơn này"
            return
        q = urllib.parse.urlencode({"fileGuid": j["fileGuid"], "fileName": j.get("fileName") or "hoadon.xml"})
        d3, _c3, u3 = lan.goi(goc + "/Invoice/Download?" + q)
        if d3 is not None and not lan.nhan(d3, u3, chi="xml"):
            lan.ly_do = "cổng EasyInvoice trả file rỗng (phiên tải không được giữ)"
        return
    if code:
        goc = f"{u.scheme}://{u.netloc}"
        d5, _c5, u5 = lan.goi(goc + "/tai-pdf?" + urllib.parse.urlencode({"ma": code}))
        if d5 is not None:
            lan.nhan(d5, u5, chi="pdf")


def tai_hoa_don(link: str | None, ma: str | None = None, tu_email: str | None = None, phien=None, han_s: float = 45) -> dict:
    """Tải file hóa đơn theo link / mã tra cứu ở cổng đã hỗ trợ.
    → {ok, cong, tep: [{loai: 'xml'|'pdf', data, content_type, nguon}], ho_tro, ly_do, da_thu: [{url, kq}], tam_ngung, cho_s}
    `tam_ngung` = True: cổng đang giới hạn số lần gọi / nghẽn (xem `TamNgung`) — không phải lỗi của hóa đơn, thử lại sau.
    `phien`: đối tượng có `.goi(url, du_lieu=None) -> (data, content_type, url_cuoi)` (mặc định `Phien()` gọi HTTP thật)."""
    link = go_boc(link)
    kq = {"ok": False, "cong": None, "tep": [], "ho_tro": True, "ly_do": None, "da_thu": [], "tam_ngung": False, "cho_s": None}
    cong = cong_ho_tro(link, ma, tu_email)
    kq["cong"] = cong
    if cong is None:
        kq["ho_tro"] = False
        try:
            host = (urllib.parse.urlsplit(link).hostname or "") if link else ""
        except ValueError:
            host = ""
        kq["ly_do"] = (f"cổng {host[:60]} chưa hỗ trợ tự tải (cần mã xác minh / đăng nhập) — bấm link tải tay rồi 📎 AI đọc" if host
                       else "không có link tra cứu của cổng đã hỗ trợ — tải tay rồi 📎 AI đọc")[:200]
        return kq
    lan = _Lan(phien or Phien(), han_s)
    code = (ma_tu_link(link) if link else None) or (ma or "").strip()
    if cong == "MISA":
        _misa(lan, code)
    else:
        _easyinvoice(lan, link, code)
    kq["da_thu"] = lan.da_thu
    kq["tep"] = [lan.tep[k] for k in ("xml", "pdf") if k in lan.tep]
    kq["ok"] = bool(kq["tep"])
    if not kq["ok"]:
        loi = next((x["kq"] for x in lan.da_thu if x["kq"].startswith("lỗi")), None)
        kq["ly_do"] = (lan.ly_do or loi or "cổng không trả file cho link / mã này")[:200]
        if lan.tam_ngung:
            kq["tam_ngung"], kq["cho_s"] = True, lan.cho_s
            kq["ly_do"] = (f"{TEN_CONG.get(cong, cong)}: {lan.tam_ngung} — chưa tính là lỗi, app tự thử lại sau")[:200]
    return kq


TEN_CONG = {"MISA": "MISA meInvoice", "EASYINVOICE": "EasyInvoice"}
