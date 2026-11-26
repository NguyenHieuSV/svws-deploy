"""⬇ TỰ TẢI HÓA ĐƠN từ LINK / MÃ TRA CỨU trong thư cổng hóa đơn điện tử (anh Hiếu 26/11/2026).

Thư cổng HĐĐT (MISA meInvoice, EasyInvoice…) thường KHÔNG đính kèm file: chỉ có link tra cứu + mã. Module này thử tải thẳng
file hóa đơn (XML trước, rồi PDF) để app đọc số tiền chính xác và lưu file kèm dòng hàng chờ — kế toán khỏi mở link, dán mã.

AN TOÀN (link nằm trong thư = dữ liệu KHÔNG tin cậy):
  • chỉ tải từ các TÊN MIỀN CỔNG HĐĐT trong `MIEN_CHO_PHEP`; mọi bước chuyển hướng cũng phải thuộc danh sách;
  • chỉ http/https cổng mặc định, mỗi lần ≤ `TIMEOUT` giây, mỗi file ≤ `GIOI_HAN` (8 MB), cả lượt ≤ `han_s` giây;
  • nhận dạng file theo CHỮ KÝ ĐẦU FILE (PDF / XML / ZIP), không tin Content-Type; trang HTML chỉ dò link tải đúng 1 cấp;
  • cổng đòi mã xác minh hình ảnh (captcha) hay đăng nhập thì KHÔNG tải được → trả lý do, kế toán làm tay như cũ.

Không ghi CSDL, không gọi AI ở đây — nơi gọi (`ke_toan_quy._hdc_tu_tai`) đọc file và điền dòng.
"""
import io
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

GIOI_HAN = 8 * 1024 * 1024          # 8 MB / file
TIMEOUT = 20                        # giây / lần gọi
SO_CHUYEN_HUONG = 4
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36 SVWS-HDDT/1.0"

# Tên miền cổng hóa đơn điện tử được phép tải (khớp đúng tên hoặc tên miền con). Cổng chưa có ở đây → «chưa hỗ trợ».
MIEN_CHO_PHEP = (
    "meinvoice.vn",                              # MISA meInvoice
    "easyinvoice.com.vn", "easyinvoice.vn",      # EasyInvoice (Softdreams): <MST>hd.easyinvoice.com.vn
    "vnpt-invoice.com.vn",                       # VNPT Invoice
    "sinvoice.viettel.vn", "vinvoice.viettel.vn",  # Viettel
    "ehoadon.vn",                                # BKAV eHoadon
    "einvoice.fpt.com.vn",                       # FPT eInvoice
    "mobifoneinvoice.vn",                        # MobiFone Invoice
    "minvoice.com.vn", "minvoice.vn",            # M-Invoice
    "hilo.com.vn", "vninvoice.vn", "wininvoice.vn", "cyberbill.vn", "hoadon30s.vn",
)
_THAM_SO_MA = ("sc", "code", "ma", "matracuu", "ma_tra_cuu", "strfkey", "fkey", "key")


def thuoc_cong(host: str, mien=None) -> bool:
    host = (host or "").strip(".").lower()
    for d in ([mien] if mien else MIEN_CHO_PHEP):
        if host == d or host.endswith("." + d):
            return True
    return False


def kiem_url(url: str) -> str | None:
    """URL hợp lệ để tải → None; không hợp lệ → lý do. Chỉ http/https, cổng mặc định, tên miền cổng HĐĐT."""
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
        return f"cổng {(u.hostname or '?')[:60]} chưa nằm trong danh sách tự tải"
    return None


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


def ung_vien(link: str | None, ma: str | None = None, tu_email: str | None = None) -> list[str]:
    """Các URL sẽ thử theo thứ tự (XML trước PDF, link gốc sau cùng). Chỉ gồm URL thuộc cổng được phép."""
    link = (link or "").strip()
    ma = (ma or "").strip()
    ra = []
    try:
        u = urllib.parse.urlsplit(link) if link else None
    except ValueError:
        u = None
    host = (u.hostname or "").lower() if u else ""
    mien_gui = (tu_email or "").split("@")[-1].strip().lower()
    code = (ma_tu_link(link) if link else None) or ma
    q = urllib.parse.quote
    if thuoc_cong(host, "meinvoice.vn") or (not host and code and ("meinvoice" in mien_gui or "misa" in mien_gui)):
        # MISA meInvoice: trang tra cứu có đường tải thẳng theo mã (XML chuẩn cơ quan thuế + PDF)
        if code:
            goc = "https://www.meinvoice.vn/tra-cuu/DownloadHandler.ashx"
            ra += [f"{goc}?Type=xml&Code={q(code)}", f"{goc}?Type=pdf&Viewer=1&Code={q(code)}", f"{goc}?Type=pdf&Code={q(code)}"]
    elif thuoc_cong(host, "easyinvoice.com.vn") or thuoc_cong(host, "easyinvoice.vn"):
        # EasyInvoice: thư ghi sẵn «…/tai-pdf?ma=<mã>» để tải nhanh PDF; thử cả bản XML cùng mã
        if code and u:
            goc = f"{u.scheme}://{u.netloc}"
            ra += [f"{goc}/tai-xml?ma={q(code)}", f"{goc}/tai-pdf?ma={q(code)}"]
    if link and kiem_url(link) is None:
        ra.append(link)
    sach, da = [], set()
    for x in ra:
        if x not in da and kiem_url(x) is None:
            da.add(x)
            sach.append(x)
    return sach


class _KhongChuyenHuong(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):      # tự xử lý chuyển hướng để kiểm từng chặng
        return None


def _lay_http(url: str) -> tuple[bytes, str, str]:
    """GET một URL (tự theo chuyển hướng ≤ SO_CHUYEN_HUONG chặng, MỖI chặng phải thuộc cổng được phép).
    → (dữ liệu ≤ GIOI_HAN, content-type, url cuối). Lỗi → ValueError(lý do ngắn)."""
    mo = urllib.request.build_opener(_KhongChuyenHuong)
    for _ in range(SO_CHUYEN_HUONG + 1):
        ly = kiem_url(url)
        if ly:
            raise ValueError(ly)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*", "Accept-Language": "vi,en;q=0.8"})
        try:
            with mo.open(req, timeout=TIMEOUT) as r:
                data = r.read(GIOI_HAN + 1)
                if len(data) > GIOI_HAN:
                    raise ValueError("file lớn hơn 8 MB")
                return data, (r.headers.get("Content-Type") or ""), url
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
                url = urllib.parse.urljoin(url, e.headers["Location"])
                continue
            raise ValueError(f"cổng trả lỗi HTTP {e.code}")
        except urllib.error.URLError as e:
            raise ValueError(f"không kết nối được cổng ({str(getattr(e, 'reason', e))[:60]})")
        except (TimeoutError, OSError) as e:
            raise ValueError(f"cổng không trả lời ({type(e).__name__})")
    raise ValueError("chuyển hướng quá nhiều lần")


def nhan_dang(data: bytes) -> str | None:
    """Loại file theo chữ ký đầu file: 'pdf' · 'zip' · 'xml' · 'html' · None (rỗng / lạ)."""
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


_RE_LINK = re.compile(r"""(?:href|src|data-url|data-href)\s*=\s*["']([^"'<>\s]{4,400})["']""", re.I)
_RE_TAI = re.compile(r"xml|pdf|download|tai-|taihoadon|tai_hoa_don|getfile|export|handler", re.I)


def link_trong_html(html: bytes, goc: str) -> list[str]:
    """Link tải (xml / pdf / download…) trong trang tra cứu — tuyệt đối hóa theo `goc`, chỉ giữ link cổng được phép, ≤ 4."""
    try:
        s = html[:400000].decode("utf-8", errors="replace")
    except Exception:
        return []
    ra = []
    for m in _RE_LINK.finditer(s):
        h = m.group(1).replace("&amp;", "&")
        if h.startswith(("#", "javascript:", "mailto:", "data:")) or not _RE_TAI.search(h):
            continue
        if re.search(r"\.(css|js|png|jpe?g|gif|svg|ico|woff2?)(\?|$)", h, re.I):
            continue
        u = urllib.parse.urljoin(goc, h)
        if u not in ra and kiem_url(u) is None:
            ra.append(u)
        if len(ra) >= 4:
            break
    return ra


def _an_ma(url: str) -> str:
    """Rút gọn URL để ghi nhật ký (không cần lộ cả mã)."""
    u = urllib.parse.urlsplit(url)
    return f"{u.hostname}{u.path}"[:90]


def tai_hoa_don(link: str | None, ma: str | None = None, tu_email: str | None = None, lay=None, han_s: float = 45) -> dict:
    """Thử tải file hóa đơn theo link / mã tra cứu.
    → {ok, tep: [{loai: 'xml'|'pdf', data, content_type, nguon}], ho_tro, ly_do, da_thu: [{url, kq}]}
    `lay(url) -> (data, content_type, url_cuoi)` thay được khi thử (mặc định gọi HTTP thật)."""
    lay = lay or _lay_http
    kq = {"ok": False, "tep": [], "ho_tro": True, "ly_do": None, "da_thu": []}
    ds = ung_vien(link, ma, tu_email)
    if not ds:
        kq["ho_tro"] = False
        ly = kiem_url(link) if link else None
        kq["ly_do"] = (ly or "không có link tra cứu, mã tra cứu không đủ để tải")[:200]
        return kq
    co = {}
    bat_dau = time.monotonic()
    da_do_html = False
    i = 0
    while i < len(ds) and i < 8:
        url = ds[i]
        i += 1
        if time.monotonic() - bat_dau > han_s:
            kq["da_thu"].append({"url": _an_ma(url), "kq": "hết thời gian"})
            break
        try:
            data, ct, cuoi = lay(url)
        except ValueError as e:
            kq["da_thu"].append({"url": _an_ma(url), "kq": "lỗi: " + str(e)[:80]})
            continue
        except Exception as e:                                           # noqa: BLE001 — không để lỗi lạ làm hỏng lượt quét
            kq["da_thu"].append({"url": _an_ma(url), "kq": f"lỗi: {type(e).__name__}"})
            continue
        loai = nhan_dang(data)
        kq["da_thu"].append({"url": _an_ma(url), "kq": loai or "rỗng / không nhận ra"})
        if loai == "zip":
            for l2, d2 in tu_zip(data):
                co.setdefault(l2, {"loai": l2, "data": d2, "nguon": _an_ma(url),
                                   "content_type": "application/xml" if l2 == "xml" else "application/pdf"})
        elif loai in ("xml", "pdf"):
            co.setdefault(loai, {"loai": loai, "data": data, "nguon": _an_ma(url),
                                 "content_type": "application/xml" if loai == "xml" else "application/pdf"})
        elif loai == "html" and not da_do_html:
            da_do_html = True                                            # dò link tải trong trang tra cứu — đúng 1 cấp
            for u2 in link_trong_html(data, cuoi or url):
                if u2 not in ds:
                    ds.append(u2)
        if "xml" in co and "pdf" in co:
            break
    kq["tep"] = [co[k] for k in ("xml", "pdf") if k in co]
    kq["ok"] = bool(kq["tep"])
    if not kq["ok"]:
        co_html = any(x["kq"] == "html" for x in kq["da_thu"])
        kq["ly_do"] = ("cổng chỉ trả trang web (cần nhập mã xác minh / đăng nhập) — tải tay rồi bấm 📎 AI đọc" if co_html
                       else "cổng không trả file cho link / mã này" if all(not x["kq"].startswith("lỗi") for x in kq["da_thu"])
                       else (next((x["kq"] for x in kq["da_thu"] if x["kq"].startswith("lỗi")), "không tải được")))[:200]
    return kq
