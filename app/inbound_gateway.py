"""
CỔNG THƯ ĐẾN — thu thư phản hồi của khách vào hệ thống.
Dev: FakeInboundProvider (vài thư mẫu). Prod: ImapInboundProvider (poll IMAP hộp thư chung).
Mỗi thư là dict: tu_email, tieu_de, noi_dung, message_id, in_reply_to.
"""
import email, imaplib
from email.header import decode_header, make_header
from email.utils import parseaddr
from typing import Protocol
from .config import settings


class InboundProvider(Protocol):
    ten: str
    def lay_thu_moi(self) -> list[dict]: ...


class FakeInboundProvider:
    ten = "DEMO"
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


def _body(m) -> str:
    if m.is_multipart():
        for p in m.walk():
            if p.get_content_type() == "text/plain":
                try: return p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8", "ignore")
                except Exception: continue
        return ""
    try: return m.get_payload(decode=True).decode(m.get_content_charset() or "utf-8", "ignore")
    except Exception: return m.get_payload() or ""


class ImapInboundProvider:
    ten = "IMAP"
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


def lay_inbound_provider() -> InboundProvider:
    return ImapInboundProvider() if settings.inbound_provider.upper() == "IMAP" else FakeInboundProvider()
