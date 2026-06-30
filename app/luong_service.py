"""
Tính lương Việt Nam (bản đầy đủ) — prorate theo công, tăng ca theo hệ số,
BHXH/BHYT/BHTN (NLĐ + DN) có trần đóng, thuế TNCN lũy tiến từng phần.
Miễn thuế: phụ cấp cơm trưa ≤ 730.000đ/tháng và phần TĂNG CA vượt đơn giá giờ thường.
Các hằng số để dạng module-level → dễ cập nhật khi luật/lương cơ sở thay đổi.
"""
from decimal import Decimal, ROUND_HALF_UP

D = lambda x: Decimal(str(x or 0))

# Tỷ lệ NLĐ đóng
TL_BHXH_NV = Decimal("0.08"); TL_BHYT_NV = Decimal("0.015"); TL_BHTN_NV = Decimal("0.01")
# Tỷ lệ DN đóng
TL_BHXH_DN = Decimal("0.175"); TL_BHYT_DN = Decimal("0.03"); TL_BHTN_DN = Decimal("0.01")
# Trần lương đóng BH (2025): BHXH/BHYT = 20× lương cơ sở (2.34tr) ; BHTN = 20× LTT vùng I (4.96tr)
TRAN_BHXH_BHYT = Decimal("46800000")
TRAN_BHTN = Decimal("99200000")
# Giảm trừ gia cảnh
GIAM_TRU_BAN_THAN = Decimal("11000000")
GIAM_TRU_PHU_THUOC = Decimal("4400000")
# Miễn thuế phụ cấp cơm trưa
MIEN_THUE_AN = Decimal("730000")
# Hệ số tăng ca
HS_OT_THUONG = Decimal("1.5"); HS_OT_CUOI_TUAN = Decimal("2.0"); HS_OT_LE = Decimal("3.0")
GIO_CONG_NGAY = Decimal("8")

BIEU_THUE = [
    (Decimal("5000000"), Decimal("0.05")), (Decimal("10000000"), Decimal("0.10")),
    (Decimal("18000000"), Decimal("0.15")), (Decimal("32000000"), Decimal("0.20")),
    (Decimal("52000000"), Decimal("0.25")), (Decimal("80000000"), Decimal("0.30")),
    (None, Decimal("0.35")),
]


def _r(x) -> Decimal:
    return Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def tinh_tncn(thu_nhap_tinh_thue: Decimal, bieu=None) -> Decimal:
    bieu = bieu or BIEU_THUE
    tn = max(Decimal(0), thu_nhap_tinh_thue); thue = Decimal(0); truoc = Decimal(0)
    for tran, suat in bieu:
        tran = None if tran is None else D(tran)
        suat = D(suat)
        if tran is None or tn <= tran:
            thue += (tn - truoc) * suat; break
        thue += (tran - truoc) * suat; truoc = tran
    return _r(thue)


def tinh_luong(luong_co_ban, luong_dong_bh=0, cong_chuan=26, cong_thuc_te=26,
               gio_ot_thuong=0, gio_ot_cuoi_tuan=0, gio_ot_le=0,
               phu_cap_an=0, phu_cap_di_lai=0, phu_cap_dien_thoai=0, phu_cap_trach_nhiem=0,
               so_phu_thuoc=0, tam_ung=0,
               phu_cap_khac=0, ngay_nghi_kpep=0, so_phut_di_tre=0, khau_tru_khac=0,
               cfg=None) -> dict:
    # Tham số theo luật — lấy từ cfg (cấu hình cập nhật được), thiếu thì dùng mặc định
    c = cfg or {}
    def cv(k, d):
        return D(c[k]) if c.get(k) is not None else d
    tl_bhxh_nv = cv("tl_bhxh_nv", TL_BHXH_NV); tl_bhyt_nv = cv("tl_bhyt_nv", TL_BHYT_NV); tl_bhtn_nv = cv("tl_bhtn_nv", TL_BHTN_NV)
    tl_bhxh_dn = cv("tl_bhxh_dn", TL_BHXH_DN); tl_bhyt_dn = cv("tl_bhyt_dn", TL_BHYT_DN); tl_bhtn_dn = cv("tl_bhtn_dn", TL_BHTN_DN)
    tran_xhyt = cv("tran_bhxh_bhyt", TRAN_BHXH_BHYT); tran_tn = cv("tran_bhtn", TRAN_BHTN)
    gt_bt = cv("giam_tru_ban_than", GIAM_TRU_BAN_THAN); gt_pt = cv("giam_tru_phu_thuoc", GIAM_TRU_PHU_THUOC)
    mien_an_max = cv("mien_thue_an", MIEN_THUE_AN)
    hs_th = cv("hs_ot_thuong", HS_OT_THUONG); hs_ct = cv("hs_ot_cuoi_tuan", HS_OT_CUOI_TUAN); hs_le = cv("hs_ot_le", HS_OT_LE)
    bieu = c.get("bac_thue") or BIEU_THUE

    lcb = D(luong_co_ban)
    cc = D(cong_chuan) or Decimal(26)
    ctt = D(cong_thuc_te)
    ldbh = D(luong_dong_bh) or lcb              # 0 → lấy lương cơ bản
    # Lương theo công thực tế (số công được trả)
    luong_theo_cong = _r(lcb * ctt / cc)
    # Đơn giá ngày / phút (theo lương cơ bản tháng)
    don_gia_ngay = lcb / cc
    don_gia_gio = lcb / cc / GIO_CONG_NGAY
    don_gia_phut = don_gia_gio / Decimal(60)
    # Khấu trừ nghỉ không phép & đi làm trễ (giảm thu nhập trước thuế — coi như không có thu nhập phần đó)
    khau_tru_nghi = _r(D(ngay_nghi_kpep) * don_gia_ngay)
    khau_tru_tre = _r(D(so_phut_di_tre) * don_gia_phut)
    luong_thuc_te = max(Decimal(0), luong_theo_cong - khau_tru_nghi - khau_tru_tre)
    g_th, g_ct, g_le = D(gio_ot_thuong), D(gio_ot_cuoi_tuan), D(gio_ot_le)
    tien_ot = _r(don_gia_gio * (g_th * hs_th + g_ct * hs_ct + g_le * hs_le))
    # Phần OT được MIỄN thuế = phần vượt trên đơn giá giờ thường (hệ số − 1)
    ot_mien_thue = _r(don_gia_gio * (g_th * (hs_th - 1) + g_ct * (hs_ct - 1) + g_le * (hs_le - 1)))
    # Phụ cấp (cố định + phát sinh trong kỳ)
    pc_an = D(phu_cap_an)
    pc_co_dinh = pc_an + D(phu_cap_di_lai) + D(phu_cap_dien_thoai) + D(phu_cap_trach_nhiem)
    pc_khac = D(phu_cap_khac)
    pc = pc_co_dinh + pc_khac
    an_mien_thue = min(pc_an, mien_an_max)
    tong_thu_nhap = luong_thuc_te + tien_ot + pc

    # Bảo hiểm — áp trần đóng
    base_xhyt = min(ldbh, tran_xhyt)
    base_tn = min(ldbh, tran_tn)
    bhxh = _r(base_xhyt * tl_bhxh_nv); bhyt = _r(base_xhyt * tl_bhyt_nv); bhtn = _r(base_tn * tl_bhtn_nv)
    bh_nv = bhxh + bhyt + bhtn
    bhxh_dn = _r(base_xhyt * tl_bhxh_dn); bhyt_dn = _r(base_xhyt * tl_bhyt_dn); bhtn_dn = _r(base_tn * tl_bhtn_dn)
    bh_dn = bhxh_dn + bhyt_dn + bhtn_dn

    # Thuế TNCN
    giam_tru = gt_bt + gt_pt * D(so_phu_thuoc)
    thu_nhap_chiu_thue = tong_thu_nhap - an_mien_thue - ot_mien_thue   # phần miễn thuế trừ ra
    thu_nhap_tinh_thue = thu_nhap_chiu_thue - bh_nv - giam_tru
    thue = tinh_tncn(thu_nhap_tinh_thue, bieu)

    tu = D(tam_ung)
    ktkhac = D(khau_tru_khac)
    khau_tru = bh_nv + thue + tu + ktkhac
    thuc_linh = tong_thu_nhap - khau_tru
    chi_phi_dn = tong_thu_nhap + bh_dn      # tổng chi phí lương cho DN

    return {
        "luong_co_ban": lcb, "luong_theo_cong": luong_theo_cong, "luong_thuc_te": luong_thuc_te,
        "cong_chuan": cc, "cong_thuc_te": ctt,
        "gio_ot_thuong": g_th, "gio_ot_cuoi_tuan": g_ct, "gio_ot_le": g_le,
        "ot": tien_ot, "phu_cap": pc, "phu_cap_co_dinh": pc_co_dinh, "phu_cap_khac": pc_khac,
        "ngay_nghi_kpep": D(ngay_nghi_kpep), "so_phut_di_tre": int(so_phut_di_tre or 0),
        "khau_tru_nghi": khau_tru_nghi, "khau_tru_tre": khau_tru_tre, "khau_tru_khac": ktkhac,
        "tong_thu_nhap": tong_thu_nhap,
        "bhxh": bhxh, "bhyt": bhyt, "bhtn": bhtn,
        "bhxh_dn": bhxh_dn, "bhyt_dn": bhyt_dn, "bhtn_dn": bhtn_dn,
        "thu_nhap_chiu_thue": _r(max(Decimal(0), thu_nhap_tinh_thue)),
        "thue_tncn": thue, "tam_ung": tu,
        "khau_tru": khau_tru, "thuc_linh": thuc_linh, "chi_phi_dn": chi_phi_dn,
    }
