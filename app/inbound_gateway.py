"""
CỔNG THƯ ĐẾN — thu thư phản hồi của khách vào hệ thống.
Dev: FakeInboundProvider (vài thư mẫu). Prod: ImapInboundProvider (poll IMAP hộp thư chung).
Mỗi thư là dict: tu_email, tieu_de, noi_dung, message_id, in_reply_to.
"""
import email, imaplib
import html as _html
import re as _re
from email.header import decode_header, make_header
from email.utils import parseaddr, getaddresses
from typing import Protocol
from .config import settings


class InboundProvider(Protocol):
    ten: str
    def lay_thu_moi(self) -> list[dict]: ...


class FakeInboundProvider:
    ten = "DEMO"
    def lay_thu(self, tu_ngay=None, den_ngay=None, bao=None, bo_qua_mid=None) -> list[dict]:
        return self.lay_thu_moi()

    def lay_thu_moi(self) -> list[dict]:
        return [
            {"tu_email": "detmayx@kh.vn",
             "tieu_de": "Re: Giải pháp xử lý nước cho Cty Dệt may X",
             "noi_dung": "Cảm ơn SVWS. Bên tôi quan tâm, vui lòng gửi báo giá chi tiết "
                         "cho công suất 500 m3/ngày và thời gian thi công.",
             "message_id": "<demo-reply-1@kh.vn>", "in_reply_to": None},
            {"tu_email": "phongmua@congtymoi.vn",
             "tieu_de": "Hỏi về hệ thống RO công nghiệp",
             "noi_dung": "Chúng tôi cần tư vấn hệ RO cho nhà máy mới. Vui lòng liên hệ lại.",
             "message_id": "<demo-reply-2@congtymoi.vn>", "in_reply_to": None},
        ]


def _txt(v):
    try: return str(make_header(decode_header(v or "")))
    except Exception: return v or ""


def _bo_html(t: str) -> str:
    """Bóc thẻ HTML/CSS ra chữ thường — thư HĐĐT (MISA/VNPT…) thường chỉ có thân HTML.
    Link của thẻ <a> giữ lại sau chữ: «link (https://…hd.easyinvoice.com.vn/…)» — thư cổng HĐĐT chỉ ghi chữ «link»,
    bỏ thẻ đi là mất link tra cứu / tải PDF (05/11/2026)."""
    t = _re.sub(r"(?is)<(style|script|head).*?</\1>", " ", t)
    t = _re.sub(r"(?is)<a\b[^>]*?href\s*=\s*[\"']?(https?://[^\"'\s>]+)[\"']?[^>]*>(.*?)</a>",
                lambda m: f" {m.group(2)} ({m.group(1)}) " if m.group(1) not in m.group(2) else f" {m.group(2)} ", t)
    t = _re.sub(r"(?i)<br\s*/?>|</p>|</tr>|</div>|</li>|</h[1-6]>", "\n", t)
    t = _re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)
    return "\n".join(" ".join(d.split()) for d in t.splitlines() if d.strip())


def _body(m) -> str:
    if m.is_multipart():
        van_plain, van_html = "", ""
        for p in m.walk():
            ct = p.get_content_type()
            if ct == "text/plain" and not van_plain:
                try: van_plain = p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "ignore")
                except Exception: continue
            if ct == "text/html" and not van_html:
                try: van_html = p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "ignore")
                except Exception: pass
        # Thư cổng HĐĐT (EasyInvoice…) có phần chữ thường bị cắt gọn (thiếu số tiền / ngày) → lấy bản DÀI HƠN trong hai bản;
        # bản HTML đã bóc thẻ, giữ link <a>. Chỉ có một bản thì dùng bản đó.
        van_html_chu = _bo_html(van_html) if van_html else ""
        if van_plain.strip() and len(van_plain.strip()) >= len(van_html_chu.strip()):
            return van_plain
        return van_html_chu or van_plain
    try: t = m.get_payload(decode=True).decode(m.get_content_charset() or "utf-8", "ignore")
    except Exception: return m.get_payload() or ""
    return _bo_html(t) if m.get_content_type() == "text/html" else t


def _thu_long(m) -> str:
    """Ghép tiêu đề + thân các THƯ ĐÍNH KÈM (forward dạng .eml / message/rfc822)
    để AI đọc được cả nội dung thư gốc bên trong."""
    if not m.is_multipart():
        return ""
    ra = []
    for p in m.walk():
        m2 = None
        if p.get_content_type() == "message/rfc822":
            pl = p.get_payload()
            m2 = pl[0] if isinstance(pl, list) and pl else (pl if hasattr(pl, "walk") else None)
        elif str(p.get_filename() or "").lower().endswith(".eml"):
            try:
                m2 = email.message_from_bytes(p.get_payload(decode=True) or b"")
            except Exception:
                m2 = None
        if m2 is not None:
            ra.append(f"--- Thư đính kèm: {_txt(m2.get('Subject'))} ---\n{_body(m2)}")
        if len(ra) >= 2:
            break
    return "\n\n".join(ra)


class ImapInboundProvider:
    ten = "IMAP"
    def lay_thu(self, tu_ngay=None, den_ngay=None, bao=None, bo_qua_mid=None) -> list[dict]:
        return _imap_lay_thu(tu_ngay, den_ngay, bao, bo_qua_mid=bo_qua_mid)

    def lay_thu_moi(self) -> list[dict]:
        out = []
        M = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
        M.login(settings.imap_user, settings.imap_pass)
        M.select("INBOX")
        typ, data = M.search(None, "UNSEEN")
        for num in data[0].split():
            typ, md = M.fetch(num, "(RFC822)")
            m = email.message_from_bytes(md[0][1])
            # bỏ qua thư tự động để tránh vòng lặp
            if (m.get("Auto-Submitted", "no").lower() != "no"
                    or "bulk" in (m.get("Precedence", "").lower())):
                continue
            out.append({"tu_email": parseaddr(m.get("From"))[1],
                        "tieu_de": _txt(m.get("Subject")),
                        "noi_dung": _body(m),
                        "message_id": m.get("Message-ID"),
                        "in_reply_to": m.get("In-Reply-To")})
        M.logout()
        return out


def _dinh_kem(m, mo_eml: bool = True) -> list[dict]:
    """Nhặt file đính kèm (PDF / XML / ảnh / Excel .xlsx / CSV — báo giá NCC hay gửi Excel) — tối đa 3 file,
    mỗi file ≤ 8MB. Thư đính kèm dạng file .eml cũng được MỞ RA để nhặt file nằm bên trong."""
    out = []
    if not m.is_multipart():
        return out
    for p in m.walk():
        cd = str(p.get("Content-Disposition") or "")
        fn = p.get_filename()
        ct = (p.get_content_type() or "").lower()
        # 📧 file .eml đính kèm (client lưu thư gốc thành file) → parse rồi nhặt tiếp 1 cấp
        if mo_eml and str(fn or "").lower().endswith(".eml") and ct != "message/rfc822":
            try:
                m2 = email.message_from_bytes(p.get_payload(decode=True) or b"")
                for f2 in _dinh_kem(m2, mo_eml=False):
                    out.append(f2)
                    if len(out) >= 3:
                        break
            except Exception:
                pass
            continue
        if not fn and "attachment" not in cd.lower():
            continue
        fn = _txt(fn or "dinh_kem")
        low = fn.lower()
        if not (ct == "application/pdf" or low.endswith((".pdf", ".xml"))
                or ct.startswith("image/") or low.endswith((".png", ".jpg", ".jpeg"))
                or ct in ("application/xml", "text/xml")
                or low.endswith((".xlsx", ".xlsm", ".csv"))
                or ct in ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv")):
            continue
        try:
            data = p.get_payload(decode=True) or b""
        except Exception:
            continue
        if 0 < len(data) <= 8 * 1024 * 1024:
            out.append({"ten_file": fn, "content_type": ct, "data": data})
        if len(out) >= 3:
            break
    return out


IMAP_TIMEOUT = 180      # giây cho mỗi thao tác socket — kết nối treo không giữ luồng quét nền mãi (06/11/2026)
MID_MOI_LENH = 100      # số thư hỏi Message-ID trong MỘT lệnh FETCH (header vài chục byte / thư)


def _mid_chuan(mid) -> str:
    """Message-ID như nơi gọi lưu vào CSDL (strip, cắt 250 ký tự) — để so với tập đã biết."""
    return (mid or "").strip()[:250]


def _imap_mid_theo_so(M, nums) -> dict:
    """Message-ID của từng số thư, hỏi hàng loạt bằng BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)] (mỗi lệnh MID_MOI_LENH thư,
    không tải thân / đính kèm, không đánh dấu đã đọc). → {số thư (bytes): Message-ID thô (str, có thể rỗng)}.
    Trả lời của máy chủ là dãy (b'12 (BODY[HEADER.FIELDS (MESSAGE-ID)] {n}', b'Message-ID: <…>\\r\\n\\r\\n'), b')' …"""
    ra = {}
    for i in range(0, len(nums), MID_MOI_LENH):
        lo = nums[i:i + MID_MOI_LENH]
        typ, data = M.fetch(b",".join(lo), "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")
        for p in data or []:
            if not (isinstance(p, tuple) and len(p) >= 2):
                continue
            mo = _re.match(rb"\s*(\d+)\s*\(", p[0] or b"")
            if mo is None:
                continue
            try:
                ra[mo.group(1)] = email.message_from_bytes(p[1] or b"").get("Message-ID") or ""
            except Exception:
                ra[mo.group(1)] = ""
    return ra


def _imap_lay_thu(tu_ngay=None, den_ngay=None, bao=None, bo_qua_mid=None) -> list[dict]:
    """Quét theo MỐC THỜI GIAN (SINCE tu_ngay; thêm BEFORE den_ngay = cửa sổ [tu_ngay, den_ngay) theo ngày nhận — quét nền
    chia 30 ngày thành từng cửa sổ 7 ngày để không giữ cả ~1.000 thư kèm đính kèm trong bộ nhớ) — đọc bằng BODY.PEEK nên
    KHÔNG đánh dấu đã đọc trong hộp thư; 'AI chưa đọc' do nơi gọi tự khử trùng bằng Message-ID đã lưu.
    bo_qua_mid (tập Message-ID ĐÃ BIẾT, 06/11/2026): hỏi Message-ID của cả cửa sổ trước (một lệnh / 100 thư); thư có
    Message-ID trong tập → trả bản RÚT GỌN {"message_id", "rut_gon": True, tu_email/tieu_de None, noi_dung "", dinh_kem []}
    KHÔNG tải thân + đính kèm (bản thật 30 ngày ≈ 1.000 thư, ~85 % đã xử lý mà vẫn tải cả đính kèm → ~9 phút);
    thư còn lại tải đủ như cũ. None → tải đủ mọi thư (endpoint cũ, quét tuần).
    bao(i, n): báo tiến độ lấy thư (mỗi 20 thư và thư cuối); khi có bo_qua_mid gọi bao(i, n, so_thu_khong_tai_than)."""
    out = []
    M = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port, timeout=IMAP_TIMEOUT)
    M.login(settings.imap_user, settings.imap_pass)
    M.select("INBOX")
    if tu_ngay is not None:
        dk = f"SINCE {tu_ngay.strftime('%d-%b-%Y')}"
        if den_ngay is not None:
            dk += f" BEFORE {den_ngay.strftime('%d-%b-%Y')}"
        typ, data = M.search(None, f"({dk})")
    else:
        typ, data = M.search(None, "UNSEEN")
    nums = data[0].split()
    mid_theo_so = _imap_mid_theo_so(M, nums) if (bo_qua_mid and nums) else {}
    bo_qua_n = 0
    for i, num in enumerate(nums, 1):
        if bao is not None and (i % 20 == 0 or i == len(nums)):
            try:
                bao(i, len(nums), bo_qua_n) if bo_qua_mid is not None else bao(i, len(nums))
            except Exception:
                pass
        mid0 = mid_theo_so.get(num)
        if mid0 and _mid_chuan(mid0) in bo_qua_mid:
            bo_qua_n += 1
            out.append({"message_id": mid0, "rut_gon": True, "tu_email": None, "den_email": "", "tieu_de": None,
                        "noi_dung": "", "dinh_kem": [], "ngay": None, "in_reply_to": None})
            continue
        typ, md = M.fetch(num, "(BODY.PEEK[])")
        m = email.message_from_bytes(md[0][1])
        if (m.get("Auto-Submitted", "no").lower() != "no"
                or "bulk" in (m.get("Precedence", "").lower())):
            continue
        nd = _body(m)
        kem = _thu_long(m)
        if kem:
            nd = (nd + "\n\n" + kem).strip()
        try:
            den = ", ".join(a for _, a in getaddresses([m.get("To") or "", m.get("Cc") or ""]) if a)[:300]
        except Exception:
            den = ""
        out.append({"tu_email": parseaddr(m.get("From"))[1],
                    "den_email": den,
                    "tieu_de": _txt(m.get("Subject")),
                    "noi_dung": nd,
                    "dinh_kem": _dinh_kem(m),
                    "ngay": m.get("Date"),
                    "message_id": m.get("Message-ID"),
                    "in_reply_to": m.get("In-Reply-To")})
    M.logout()
    return out


def lay_inbound_provider() -> InboundProvider:
    return ImapInboundProvider() if settings.inbound_provider.upper() == "IMAP" else FakeInboundProvider()


def _hop_theo_co(M, co: str) -> str | None:
    """Tên hộp thư mang cờ đặc biệt («All» = Tất cả thư, «Junk» = Thư rác) — Gmail và phần lớn máy chủ IMAP khai trong LIST."""
    try:
        typ, ds = M.list()
    except Exception:
        return None
    for d in ds or []:
        s = d.decode("utf-8", errors="replace") if isinstance(d, bytes) else str(d)
        if co.lower() in s.lower():
            m = _re.search(r'"([^"]+)"\s*$', s) or _re.search(r"(\S+)\s*$", s)
            if m:
                return m.group(1)
    return None


def tim_thu(tu_khoa: str, tu_ngay=None, toi_da: int = 30, ca_hop: bool = True, han_s: float = 60) -> list[dict]:
    """🔎 TÌM THƯ trong hộp thư theo từ khóa (người gửi / tiêu đề / thân) — để soi vì sao một hóa đơn chưa vào hàng chờ.
    Chỉ đọc (BODY.PEEK, mở hộp ở chế độ readonly) — không đánh dấu đã đọc, không đổi gì trong hộp thư.
    Khác `_imap_lay_thu`: trả CẢ thư tự động (Auto-Submitted / Precedence: bulk — luồng quét đang bỏ qua) kèm cờ `tu_dong`;
    `ca_hop`: tìm thêm ở «Tất cả thư» và «Thư rác» (thư không nằm trong Hộp thư đến thì luồng quét không thấy).
    → mới nhất trước, mỗi thư: hop, ngay, tu_email, den_email, tieu_de, message_id, tu_dong, dinh_kem [{ten, kb}], noi_dung (≤ 3.000 ký tự).
    Dừng sau `han_s` giây (request web bị cắt ~100 giây) — thư chưa kịp đọc thì bỏ, thu hẹp từ khóa / mốc ngày để tìm tiếp."""
    import time as _time
    tu_khoa = (tu_khoa or "").strip()
    if len(tu_khoa) < 3:
        raise ValueError("Từ khóa tìm thư cần ít nhất 3 ký tự")
    if settings.inbound_provider.upper() != "IMAP":
        return []
    het = _time.monotonic() + han_s
    M = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port, timeout=30)
    M.login(settings.imap_user, settings.imap_pass)
    ra, da_co = [], set()
    hop_ds = [("INBOX", "Hộp thư đến")]
    if ca_hop:
        for co, ten in ((chr(92) + "All", "Tất cả thư (không ở Hộp thư đến)"), (chr(92) + "Junk", "Thư rác")):
            h = _hop_theo_co(M, co)
            if h:
                hop_ds.append((h, ten))
    try:
        for hop, ten_hop in hop_ds:
            try:
                typ, _d = M.select(f'"{hop}"' if " " in hop or "[" in hop else hop, readonly=True)
            except Exception:
                continue
            if typ != "OK":
                continue
            dk = ["SINCE", tu_ngay.strftime("%d-%b-%Y")] if tu_ngay is not None else []
            try:
                if tu_khoa.isascii():
                    typ, data = M.search(None, *dk, "TEXT", '"' + tu_khoa.replace('"', "") + '"')
                else:
                    M.literal = tu_khoa.encode("utf-8")
                    typ, data = M.search("UTF-8", *dk, "TEXT")
            except Exception:
                continue
            nums = (data[0].split() if data and data[0] else [])[-max(1, min(int(toi_da or 30), 60)):]
            # «Tất cả thư» chứa cả thư đã thấy ở Hộp thư đến → hỏi Message-ID trước (một lệnh), thư trùng khỏi tải thân
            try:
                mid_so = _imap_mid_theo_so(M, nums) if (hop != "INBOX" and nums and da_co) else {}
            except Exception:
                mid_so = {}
            for num in reversed(nums):
                if _time.monotonic() > het or len(ra) >= 60:
                    break
                if (mid_so.get(num) or "").strip() in da_co:
                    continue
                try:
                    typ, md = M.fetch(num, "(BODY.PEEK[])")
                    m = email.message_from_bytes(md[0][1])
                except Exception:
                    continue
                mid = (m.get("Message-ID") or "").strip()
                if mid and mid in da_co:
                    continue
                if mid:
                    da_co.add(mid)
                kem = []
                for p in m.walk():
                    fn = p.get_filename()
                    if fn:
                        try:
                            kb = max(1, round(len(p.get_payload(decode=True) or b"") / 1024))
                        except Exception:
                            kb = None
                        kem.append({"ten": _txt(fn)[:120], "kb": kb})
                tu_dong = []
                if (m.get("Auto-Submitted", "no") or "no").lower() != "no":
                    tu_dong.append("Auto-Submitted: " + str(m.get("Auto-Submitted"))[:40])
                if "bulk" in (m.get("Precedence", "") or "").lower():
                    tu_dong.append("Precedence: bulk")
                try:
                    den = ", ".join(a for _, a in getaddresses([m.get("To") or "", m.get("Cc") or ""]) if a)[:300]
                except Exception:
                    den = ""
                ra.append({"hop": ten_hop, "ngay": m.get("Date"), "tu_email": parseaddr(m.get("From"))[1], "den_email": den,
                           "tieu_de": _txt(m.get("Subject")), "message_id": mid or None, "tu_dong": tu_dong,
                           "dinh_kem": kem[:10], "noi_dung": (_body(m) or "")[:3000]})
    finally:
        try:
            M.logout()
        except Exception:
            pass
    return ra
