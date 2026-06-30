"""Sinh lịch trả nợ vay theo 3 phương thức phổ biến (VAS):
- GOC_DEU : trả gốc đều mỗi kỳ, lãi tính trên dư nợ giảm dần.
- TRA_DEU : niên kim — tổng trả mỗi kỳ bằng nhau (gốc tăng dần, lãi giảm dần).
- GOC_CUOI: trả lãi mỗi kỳ, gốc trả 1 lần khi đáo hạn.
Lãi suất kỳ = lãi suất năm × số tháng mỗi kỳ / 12.
"""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

D = lambda x: Decimal(str(x or 0))
def _r(x): return Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _cuoi_thang(y, m):
    if m == 12:
        return 31
    nxt = date(y, m + 1, 1)
    from datetime import timedelta
    return (nxt - timedelta(days=1)).day


def them_thang(d: date, n: int) -> date:
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, _cuoi_thang(y, m)))


def sinh_lich(so_tien_goc, lai_suat_nam, so_ky, chu_ky_thang, ngay_nhan, phuong_thuc) -> list:
    goc = D(so_tien_goc)
    n = int(so_ky)
    r = D(lai_suat_nam) / Decimal(100) * D(chu_ky_thang) / Decimal(12)
    rows = []
    du_no = goc
    if phuong_thuc == "TRA_DEU" and r > 0:
        pmt = goc * r / (Decimal(1) - (Decimal(1) + r) ** (-n))
    for k in range(1, n + 1):
        ngay = them_thang(ngay_nhan, k * int(chu_ky_thang))
        lai = _r(du_no * r)
        if phuong_thuc == "GOC_CUOI":
            g = goc if k == n else Decimal(0)
        elif phuong_thuc == "TRA_DEU" and r > 0:
            g = _r(pmt - lai)
        else:  # GOC_DEU
            g = _r(goc / n)
        if k == n:                      # kỳ cuối: trả hết dư nợ còn lại
            g = du_no
        g = min(g, du_no)
        du_cuoi = du_no - g
        rows.append({"ky": k, "ngay_den_han": ngay, "du_no_dau": du_no,
                     "goc_phai_tra": g, "lai_phai_tra": lai, "tong_phai_tra": g + lai,
                     "du_no_cuoi": du_cuoi})
        du_no = du_cuoi
    return rows
