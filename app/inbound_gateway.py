"""
CỔNG THƯ ĐẾN — thu thư phản hồi của khách vào hệ thống.
Dev: FakeInboundProvider (vài thư mẫu). Prod: ImapInboundProvider (poll IMAP hộp thư chung).
Mỗi thư là dict: tu_email, tieu_de, noi_dung, message_id, in_reply_to.
"""
import email, imaplib
import html as _html
import re as _re
from email.header import decode_header, make_header
from email.utils import parseaddr
from typing import Protocol
from .config import settings


class InboundProvider(Protocol):
    ten: str
    def lay_thu_moi(self) -> list[dict]: ...


class FakeInboundProvider:
    ten = "DEMO"
    def lay_thu(self, tu_ngay=None) -> list[dict]:
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
    """Bóc thẻ HTML/CSS ra chữ thường — thư HĐĐT (MISA/VNPT…) thường chỉ có thân HTML."""
    t = _re.sub(r"(?is)<(style|script|head).*?</\1>", " ", t)
    t = _re.sub(r"(?i)<br\s*/?>|</p>|</tr>|</div>|</li>|</h[1-6]>", "\n", t)
    t = _re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)
    return "\n".join(" ".join(d.split()) for d in t.splitlines() if d.strip())


def _body(m) -> str:
    if m.is_multipart():
        van_html = ""
        for p in m.walk():
            ct = p.get_content_type()
            if ct == "text/plain":
                try: return p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "ignore")
                except Exception: continue
            if ct == "text/html" and not van_html:
                try: van_html = p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "ignore")
                except Exception: pass
        return _bo_html(van_html) if van_html else ""
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
    def lay_thu(self, tu_ngay=None) -> list[dict]:
        return _imap_lay_thu(tu_ngay)

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
    """Nhặt file đính kèm hóa đơn (PDF / XML / ảnh) — tối đa 3 file, mỗi file ≤ 8MB.
    Thư đính kèm dạng file .eml cũng được MỞ RA để nhặt PDF/XML nằm bên trong."""
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
                or ct in ("application/xml", "text/xml")):
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


def _imap_lay_thu(tu_ngay=None) -> list[dict]:
    """Quét theo MỐC THỜI GIAN (SINCE) — đọc bằng BODY.PEEK nên KHÔNG đánh dấu đã đọc
    trong hộp thư; 'AI chưa đọc' do nơi gọi tự khử trùng bằng Message-ID đã lưu."""
    out = []
    M = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    M.login(settings.imap_user, settings.imap_pass)
    M.select("INBOX")
    if tu_ngay is not None:
        typ, data = M.search(None, f"(SINCE {tu_ngay.strftime('%d-%b-%Y')})")
    else:
        typ, data = M.search(None, "UNSEEN")
    for num in data[0].split():
        typ, md = M.fetch(num, "(BODY.PEEK[])")
        m = email.message_from_bytes(md[0][1])
        if (m.get("Auto-Submitted", "no").lower() != "no"
                or "bulk" in (m.get("Precedence", "").lower())):
            continue
        nd = _body(m)
        kem = _thu_long(m)
        if kem:
            nd = (nd + "\n\n" + kem).strip()
        out.append({"tu_email": parseaddr(m.get("From"))[1],
                    "tieu_de": _txt(m.get("Subject")),
                    "noi_dung": nd,
                    "dinh_kem": _dinh_kem(m),
                    "message_id": m.get("Message-ID"),
                    "in_reply_to": m.get("In-Reply-To")})
    M.logout()
    return out


def lay_inbound_provider() -> InboundProvider:
    return ImapInboundProvider() if settings.inbound_provider.upper() == "IMAP" else FakeInboundProvider()
