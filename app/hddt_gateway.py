"""
CỔNG HÓA ĐƠN ĐIỆN TỬ — lớp trừu tượng để KHÔNG tự dựng engine thuế.
Thực tế: thay FakeProvider bằng SDK/API của MISA meInvoice / VNPT / Viettel
(theo NĐ 70/2025, TT 32/2025). Ứng dụng chỉ gọi qua giao diện này.
"""
from typing import Protocol


class HddtProvider(Protocol):
    ten: str
    def phat_hanh(self, hoa_don) -> dict: ...


class FakeProvider:
    """Provider giả lập cho dev. Trả mã tra cứu như nhà cung cấp thật."""
    ten = "DEMO"

    def phat_hanh(self, hoa_don) -> dict:
        return {
            "provider": self.ten,
            "ma_tra_cuu": f"{self.ten}-{hoa_don.id:08d}",
            "trang_thai": "DA_PHAT_HANH",
        }


_PROVIDERS = {"DEMO": FakeProvider()}
# Khi tích hợp thật:  _PROVIDERS["MISA"] = MisaProvider(api_key=...)


def lay_provider(ten: str | None = None) -> HddtProvider:
    return _PROVIDERS.get((ten or "DEMO").upper(), _PROVIDERS["DEMO"])
