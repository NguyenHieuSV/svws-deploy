"""
34 tỉnh/thành phố sau sắp xếp đơn vị hành chính (hiệu lực 01/07/2025) — dùng cho ô "Tỉnh/thành"
của form kỹ sư (training.py, T102 H1).

  PROVINCES          danh sách thả xuống (34 tên)
  canon_province(x)  tên bất kỳ -> tên chuẩn trong PROVINCES: nhận cả tên tỉnh CŨ (63 tỉnh trước
                     sáp nhập), không dấu, có/không "Tỉnh"/"Thành phố"/"TP."; không nhận ra -> None
"""
import re
import unicodedata
from typing import Optional

PROVINCES = [
    "An Giang", "Bắc Ninh", "Cà Mau", "Cao Bằng", "Cần Thơ", "Đà Nẵng", "Đắk Lắk", "Điện Biên",
    "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Nội", "Hà Tĩnh", "Hải Phòng", "TP. Hồ Chí Minh", "Huế",
    "Hưng Yên", "Khánh Hòa", "Lai Châu", "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Nghệ An", "Ninh Bình",
    "Phú Thọ", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sơn La", "Tây Ninh", "Thái Nguyên",
    "Thanh Hóa", "Tuyên Quang", "Vĩnh Long",
]

# Tỉnh/thành CŨ đã nhập vào đơn vị mới
_OLD_TO_NEW = {
    "Hà Giang": "Tuyên Quang", "Yên Bái": "Lào Cai", "Bắc Kạn": "Thái Nguyên",
    "Vĩnh Phúc": "Phú Thọ", "Hòa Bình": "Phú Thọ", "Bắc Giang": "Bắc Ninh", "Thái Bình": "Hưng Yên",
    "Hải Dương": "Hải Phòng", "Hà Nam": "Ninh Bình", "Nam Định": "Ninh Bình",
    "Quảng Bình": "Quảng Trị", "Quảng Nam": "Đà Nẵng", "Kon Tum": "Quảng Ngãi", "Bình Định": "Gia Lai",
    "Ninh Thuận": "Khánh Hòa", "Đắk Nông": "Lâm Đồng", "Bình Thuận": "Lâm Đồng", "Phú Yên": "Đắk Lắk",
    "Bình Dương": "TP. Hồ Chí Minh", "Bà Rịa - Vũng Tàu": "TP. Hồ Chí Minh", "Bình Phước": "Đồng Nai",
    "Long An": "Tây Ninh", "Sóc Trăng": "Cần Thơ", "Hậu Giang": "Cần Thơ", "Bến Tre": "Vĩnh Long",
    "Trà Vinh": "Vĩnh Long", "Tiền Giang": "Đồng Tháp", "Bạc Liêu": "Cà Mau", "Kiên Giang": "An Giang",
}
# Cách viết khác hay gặp
_ALIAS = {
    "Hồ Chí Minh": "TP. Hồ Chí Minh", "HCM": "TP. Hồ Chí Minh", "TPHCM": "TP. Hồ Chí Minh",
    "Sài Gòn": "TP. Hồ Chí Minh", "Saigon": "TP. Hồ Chí Minh", "Vũng Tàu": "TP. Hồ Chí Minh",
    "Bà Rịa": "TP. Hồ Chí Minh", "BRVT": "TP. Hồ Chí Minh", "Thừa Thiên Huế": "Huế",
    "Thừa Thiên - Huế": "Huế", "Đắc Lắc": "Đắk Lắk", "Daklak": "Đắk Lắk", "Đăk Nông": "Lâm Đồng",
    "Hà Nội Thủ đô": "Hà Nội", "HN": "Hà Nội",
}


def _key(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").strip().lower()).replace("đ", "d").replace("Đ", "d")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"^(tinh|thanh pho|tp\.?|t\.p\.?)\s*", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


_LOOKUP = {_key(p): p for p in PROVINCES}
_LOOKUP.update({_key(k): v for k, v in _OLD_TO_NEW.items()})
_LOOKUP.update({_key(k): v for k, v in _ALIAS.items()})


def canon_province(text: str) -> Optional[str]:
    return _LOOKUP.get(_key(text)) if text else None
