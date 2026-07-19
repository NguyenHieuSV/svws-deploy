"""Cổng gửi tin Google Chat — thay thế được, cùng khuôn với email_gateway.py.

Ba chế độ (settings.chat_provider):
  DEMO    — không gửi thật, chỉ ghi log. MẶC ĐỊNH, an toàn khi chưa cấu hình.
  WEBHOOK — đăng vào MỘT Phòng chung qua Incoming Webhook. Setup ~5 phút,
            không cần quyền admin. Không nhắn riêng được.
  APP     — Chat app + Service Account: NHẮN RIÊNG từng người theo email
            Google Workspace. Cần Workspace admin cài app cho toàn miền.

Nguyên tắc: gửi tin KHÔNG BAO GIỜ được làm hỏng nghiệp vụ. Mọi lỗi đều được
bắt lại và trả về {"da_gui": False, "loi": "..."} để nơi gọi ghi log rồi đi tiếp.
"""
import json
import time
import urllib.error
import urllib.request
from typing import Protocol

from .config import settings

_CHAT_API = "https://chat.googleapis.com/v1"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPE = "https://www.googleapis.com/auth/chat.bot"

# cache access token theo tiến trình: {"token": str, "het_han": epoch}
_token_cache: dict = {}


def _http_json(url: str, payload: dict | None = None, token: str | None = None,
               method: str = "POST", timeout: int = 20) -> dict:
    """Gọi HTTP JSON bằng thư viện chuẩn (không thêm phụ thuộc)."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8") or "{}"
    return json.loads(raw)


def _loi_ro_rang(e: Exception) -> str:
    """Đổi lỗi kỹ thuật thành câu tiếng Việt chỉ rõ phải sửa ở đâu."""
    if isinstance(e, urllib.error.HTTPError):
        try:
            chi_tiet = e.read().decode("utf-8")[:400]
        except Exception:
            chi_tiet = ""
        if e.code in (401, 403):
            return ("Google từ chối quyền (HTTP %d). Kiểm tra: Chat API đã bật chưa, "
                    "Service Account đúng chưa, và Chat app đã được admin Workspace "
                    "cài cho người nhận chưa. %s" % (e.code, chi_tiet))
        if e.code == 404:
            return ("Không tìm thấy người nhận / phòng chat (HTTP 404). Thường do email "
                    "nhân viên không khớp email Google Workspace, hoặc người đó chưa "
                    "được cài Chat app. %s" % chi_tiet)
        if e.code == 429:
            return "Google chặn tạm do gửi quá nhiều (HTTP 429). Thử lại sau ít phút."
        return f"Google Chat trả lỗi HTTP {e.code}. {chi_tiet}"
    if isinstance(e, urllib.error.URLError):
        return f"Không kết nối được tới Google Chat: {e.reason}"
    if isinstance(e, RuntimeError):      # lỗi cấu hình do chính ta nêu, đã rõ nghĩa
        return str(e)
    ten = type(e).__name__
    if "Key" in ten or "key" in str(e).lower():
        return ("Không đọc được private_key trong GCHAT_SERVICE_ACCOUNT. Thường do khi dán "
                "vào biến môi trường bị mất xuống dòng. Hãy dán lại NGUYÊN VĂN nội dung "
                f"file .json (một dòng duy nhất, giữ nguyên các ký tự \\n). [{ten}]")
    return f"{ten}: {e}"


class ChatProvider(Protocol):
    def gui_ca_nhan(self, email: str, noi_dung: str) -> dict: ...
    def gui_phong(self, noi_dung: str) -> dict: ...


class FakeChatProvider:
    """DEMO — chỉ ghi log, không gọi mạng."""
    che_do = "DEMO"

    def gui_ca_nhan(self, email, noi_dung) -> dict:
        print(f"[CHAT-DEMO] -> {email}: {noi_dung[:160]}")
        return {"da_gui": False, "che_do": "DEMO",
                "loi": "Đang ở chế độ DEMO — chưa cấu hình Google Chat nên không gửi thật."}

    def gui_phong(self, noi_dung) -> dict:
        print(f"[CHAT-DEMO] -> phòng chung: {noi_dung[:160]}")
        return {"da_gui": False, "che_do": "DEMO",
                "loi": "Đang ở chế độ DEMO — chưa cấu hình Google Chat nên không gửi thật."}


class WebhookChatProvider:
    """WEBHOOK — đăng vào một Phòng chung. Không nhắn riêng được."""
    che_do = "WEBHOOK"

    def gui_ca_nhan(self, email, noi_dung) -> dict:
        # Không có DM: ghi rõ người nhận ngay đầu tin rồi đăng vào phòng chung.
        return self.gui_phong(f"*Gửi {email}*\n{noi_dung}")

    def gui_phong(self, noi_dung) -> dict:
        url = (settings.gchat_webhook_url or "").strip()
        if not url:
            return {"da_gui": False, "che_do": self.che_do,
                    "loi": "Chưa điền GCHAT_WEBHOOK_URL trong biến môi trường."}
        try:
            _http_json(url, {"text": noi_dung})
            return {"da_gui": True, "che_do": self.che_do}
        except Exception as e:
            return {"da_gui": False, "che_do": self.che_do, "loi": _loi_ro_rang(e)}


class AppChatProvider:
    """APP — Service Account, nhắn riêng từng người theo email Workspace."""
    che_do = "APP"

    # ---- xác thực ----
    def _khoa(self) -> dict:
        raw = (settings.gchat_service_account or "").strip()
        if not raw:
            raise RuntimeError("Chưa điền GCHAT_SERVICE_ACCOUNT (nội dung file JSON key).")
        try:
            k = json.loads(raw)
        except json.JSONDecodeError:
            raise RuntimeError("GCHAT_SERVICE_ACCOUNT không phải JSON hợp lệ — "
                               "phải dán NGUYÊN nội dung file .json tải từ Google Cloud.")
        if not k.get("client_email") or not k.get("private_key"):
            raise RuntimeError("File JSON thiếu client_email hoặc private_key — "
                               "hãy tải lại khóa Service Account từ Google Cloud.")
        # Dán JSON vào biến môi trường hay bị mất xuống dòng trong private_key:
        # chuỗi còn nguyên hai ký tự \ + n. Khôi phục lại thành xuống dòng thật.
        pk = k["private_key"]
        if "\\n" in pk and "\n" not in pk:
            k["private_key"] = pk.replace("\\n", "\n")
        return k

    def _lay_token(self) -> str:
        """Đổi JWT assertion lấy access token (endpoint này nhận form-urlencoded)."""
        con = _token_cache.get("het_han", 0) - time.time()
        if _token_cache.get("token") and con > 60:
            return _token_cache["token"]
        import urllib.parse
        import jwt
        k = self._khoa()
        now = int(time.time())
        assertion = jwt.encode(
            {"iss": k["client_email"], "scope": _SCOPE, "aud": _TOKEN_URL,
             "iat": now, "exp": now + 3600},
            k["private_key"], algorithm="RS256")
        body = urllib.parse.urlencode({
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion}).encode("utf-8")
        req = urllib.request.Request(
            _TOKEN_URL, data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        _token_cache["token"] = data["access_token"]
        _token_cache["het_han"] = time.time() + int(data.get("expires_in", 3600))
        return _token_cache["token"]

    # ---- gửi ----
    def gui_ca_nhan(self, email, noi_dung) -> dict:
        email = (email or "").strip()
        if not email:
            return {"da_gui": False, "che_do": self.che_do,
                    "loi": "Nhân viên chưa có email — không xác định được người nhận trên Google Chat."}
        try:
            token = self._lay_token()
            # 1) tìm phòng nhắn riêng giữa Chat app và người này
            import urllib.parse
            q = urllib.parse.urlencode({"name": f"users/{email}"})
            dm = _http_json(f"{_CHAT_API}/spaces:findDirectMessage?{q}", None, token, method="GET")
            space = dm.get("name")
            if not space:
                return {"da_gui": False, "che_do": self.che_do,
                        "loi": f"Chưa có phòng nhắn riêng với {email} — admin Workspace cần cài Chat app cho người này."}
            # 2) gửi tin vào phòng đó
            _http_json(f"{_CHAT_API}/{space}/messages", {"text": noi_dung}, token)
            return {"da_gui": True, "che_do": self.che_do, "toi": email}
        except Exception as e:
            return {"da_gui": False, "che_do": self.che_do, "loi": _loi_ro_rang(e)}

    def gui_phong(self, noi_dung) -> dict:
        # Chế độ APP vẫn dùng webhook nếu có, để gửi thông báo chung.
        if (settings.gchat_webhook_url or "").strip():
            return WebhookChatProvider().gui_phong(noi_dung)
        return {"da_gui": False, "che_do": self.che_do,
                "loi": "Chế độ APP chỉ nhắn riêng; muốn đăng vào phòng chung hãy điền thêm GCHAT_WEBHOOK_URL."}


def lay_chat_provider() -> ChatProvider:
    ch = (settings.chat_provider or "DEMO").upper()
    if ch == "APP":
        return AppChatProvider()
    if ch == "WEBHOOK":
        return WebhookChatProvider()
    return FakeChatProvider()


def dang_bat() -> bool:
    return (settings.chat_provider or "DEMO").upper() in ("APP", "WEBHOOK")
