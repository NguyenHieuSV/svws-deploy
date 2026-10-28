"""🔄 Dấu bản dựng giao diện: dòng «<!-- build: … -->» đầu svws_app.html (đổi mỗi lần cập nhật giao diện).
Máy chủ gửi kèm mọi phản hồi qua header X-SVWS-Build (app/main.py); trang so với dấu của chính nó, khác nhau = tab
mở từ trước khi cập nhật → thanh «có bản mới — bấm tải lại» (28/10/2026: tab cũ trên iPad in nguyên JSON lỗi)."""
import os
import re

DUONG_DAN_HTML = os.path.join(os.path.dirname(__file__), "..", "svws_app.html")


def doc_build(duong_dan: str = DUONG_DAN_HTML) -> str:
    try:
        with open(duong_dan, encoding="utf-8") as f:
            for _ in range(8):
                m = re.search(r"build:\s*(\S+?)\s*-->", f.readline())
                if m:
                    return m.group(1)
    except Exception:
        pass
    return ""
