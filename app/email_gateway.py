"""
CỔNG EMAIL — gửi email chào hàng (hỗ trợ tệp đính kèm).
Dev: FakeEmailProvider (ghi log). Prod: SmtpProvider (hoặc thay SendGrid/Mailgun).
Địa chỉ gửi cấu hình ở settings.email_from.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Protocol
from .config import settings


class EmailProvider(Protocol):
    ten: str
    def gui(self, to: str, tieu_de: str, noi_dung: str, dinh_kem: list | None = None,
            gui_tu: str | None = None) -> dict: ...


class FakeEmailProvider:
    ten = "DEMO"
    def gui(self, to, tieu_de, noi_dung, dinh_kem=None, gui_tu=None) -> dict:
        n = len(dinh_kem or [])
        nguoi_gui = gui_tu or settings.email_from
        base = f"demo - không gửi thật (từ {nguoi_gui})"
        return {"trang_thai": "GUI_OK",
                "gui_tu": nguoi_gui,
                "ghi_chu": base + (f", {n} tệp đính kèm" if n else "")}


class SmtpProvider:
    ten = "SMTP"
    def gui(self, to, tieu_de, noi_dung, dinh_kem=None, gui_tu=None) -> dict:
        nguoi_gui = gui_tu or settings.email_from
        try:
            msg = MIMEMultipart()
            msg["Subject"] = tieu_de
            msg["From"] = nguoi_gui
            msg["Reply-To"] = nguoi_gui
            msg["To"] = to
            msg.attach(MIMEText(noi_dung, "plain", "utf-8"))
            for a in (dinh_kem or []):
                with open(a["duong_dan"], "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition",
                                f'attachment; filename="{os.path.basename(a["ten_file"])}"')
                msg.attach(part)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as s:
                s.starttls()
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_pass)
                s.send_message(msg)
            return {"trang_thai": "GUI_OK", "gui_tu": nguoi_gui, "ghi_chu": None}
        except Exception as e:  # noqa
            return {"trang_thai": "LOI", "gui_tu": nguoi_gui, "ghi_chu": str(e)[:200]}


def lay_email_provider() -> EmailProvider:
    return SmtpProvider() if settings.email_provider.upper() == "SMTP" else FakeEmailProvider()
