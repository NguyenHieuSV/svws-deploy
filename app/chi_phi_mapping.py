"""Danh mục 12 NHÓM CHI PHÍ để AI phân loại hóa đơn + gợi ý hồ sơ pháp lý.
Đồng bộ với bộ 'ke-toan-automation' (mapping-chi-phi.json). Backend giữ bản gọn
(mã/tên/ví dụ) phục vụ AI đoán nhóm + kiểm tra mã hợp lệ; checklist chi tiết
render ở frontend."""

NHOM = [
    {"ma": "LUONG",     "ten": "Lương – thưởng – phụ cấp",              "vi_du": "bảng lương, thưởng Tết, phụ cấp trách nhiệm"},
    {"ma": "CONGTAC",   "ten": "Công tác phí",                          "vi_du": "vé máy bay, khách sạn, taxi, lưu trú công tác"},
    {"ma": "KHOAN",     "ten": "Khoán điện thoại – xăng xe – trang phục","vi_du": "khoán điện thoại, xăng xe, đồng phục"},
    {"ma": "PHUCLOI",   "ten": "Phúc lợi (hiếu hỉ, nghỉ mát, khám SK)", "vi_du": "hiếu hỉ, du lịch nghỉ mát, khám sức khỏe, trung thu"},
    {"ma": "THUETS",    "ten": "Thuê tài sản của cá nhân",              "vi_du": "thuê xe, thuê nhà, thuê kho của cá nhân"},
    {"ma": "TIEPKHACH", "ten": "Tiếp khách – quà tặng",                 "vi_du": "ăn uống tiếp khách, quà tặng đối tác/khách hàng"},
    {"ma": "DVKT",      "ten": "Dịch vụ / nhân sự kế toán",             "vi_du": "thuê dịch vụ kế toán ngoài, lương nhân viên kế toán"},
    {"ma": "BANHANG",   "ten": "Bán hàng – chiết khấu",                 "vi_du": "chiết khấu thương mại, khuyến mại, hoa hồng"},
    {"ma": "MUAHANG",   "ten": "Mua hàng hóa / dịch vụ thường",         "vi_du": "vật tư, thiết bị, hóa chất, dịch vụ đầu vào dự án"},
    {"ma": "KHOANVIEC", "ten": "Khoán việc cho cá nhân (không HĐLĐ)",   "vi_du": "thuê cá nhân thời vụ, không ký hợp đồng lao động"},
    {"ma": "TSCD",      "ten": "TSCĐ / công cụ dụng cụ",                "vi_du": "máy móc, thiết bị, phương tiện, công cụ dụng cụ"},
    {"ma": "DUPHONG",   "ten": "Dự phòng / trích lập cuối năm",         "vi_du": "dự phòng tiền lương, nợ khó đòi, quyết toán"},
]

MA_HOP_LE = {n["ma"] for n in NHOM}
_TEN = {n["ma"]: n["ten"] for n in NHOM}

# gợi ý TK chi phí mặc định theo nhóm (để tự điền khi ghi hóa đơn mua)
TK_GOI_Y = {
    "LUONG": "642", "CONGTAC": "642", "KHOAN": "642", "PHUCLOI": "642",
    "THUETS": "642", "TIEPKHACH": "642", "DVKT": "642", "BANHANG": "641",
    "MUAHANG": "632", "KHOANVIEC": "642", "TSCD": "211", "DUPHONG": "642",
}

# từ khóa dự phòng khi CHƯA bật AI (đoán theo diễn giải/đối tác)
TU_KHOA = [
    ("LUONG",     ["lương", "thưởng", "phụ cấp"]),
    ("CONGTAC",   ["công tác", "vé máy bay", "khách sạn", "taxi", "lưu trú"]),
    ("KHOAN",     ["khoán điện thoại", "xăng xe", "đồng phục", "trang phục"]),
    ("PHUCLOI",   ["phúc lợi", "hiếu hỉ", "nghỉ mát", "du lịch", "khám sức khỏe", "trung thu"]),
    ("THUETS",    ["thuê xe", "thuê nhà", "thuê kho", "thuê tài sản"]),
    ("TIEPKHACH", ["tiếp khách", "quà tặng", "quà biếu"]),
    ("DVKT",      ["dịch vụ kế toán", "kiểm toán", "đại lý thuế"]),
    ("BANHANG",   ["chiết khấu", "khuyến mại", "hoa hồng"]),
    ("KHOANVIEC", ["khoán việc", "thời vụ", "thuê nhân công"]),
    ("TSCD",      ["máy móc", "thiết bị", "tài sản cố định", "phương tiện", "công cụ dụng cụ"]),
    ("DUPHONG",   ["dự phòng", "trích lập"]),
    ("MUAHANG",   ["vật tư", "hóa chất", "nguyên liệu", "mua hàng"]),
]


def ten(ma: str) -> str:
    return _TEN.get(ma, ma)


def danh_sach_prompt() -> str:
    return "\n".join(f'- {n["ma"]}: {n["ten"]} (ví dụ: {n["vi_du"]})' for n in NHOM)
