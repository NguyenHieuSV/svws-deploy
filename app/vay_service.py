"""Sinh lịch trả nợ vay theo 3 phương thức phổ biến (VAS):
- GOC_DEU : trả gốc đều mỗi kỳ, lãi tính trên dư nợ giảm dần.
- TRA_DEU : niên kim — tổng trả mỗi kỳ bằng nhau (gốc tăng dần, lãi giảm dần).
- GOC_CUOI: trả lãi mỗi kỳ, gốc trả 1 lần khi đáo hạn.
Chu kỳ tính theo NGÀY: lãi suất kỳ = lãi suất năm × số ngày mỗi kỳ / 365.
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


def sinh_lich(so_tien_goc, lai_suat_nam, so_ky, chu_ky_ngay, ngay_nhan, phuong_thuc,
              ngay_tra_thang=None) -> list:
    """ngay_tra_thang (1-31): trả vào NGÀY CỐ ĐỊNH hàng tháng (VD 26 = ngày 26 mỗi tháng);
    kỳ 1 = ngày đó đầu tiên SAU ngày nhận; lãi kỳ = dư nợ × lãi năm × số ngày thực ÷ 365.
    None: lịch cách đều chu_ky_ngay như cũ."""
    from datetime import timedelta
    goc = D(so_tien_goc)
    n = int(so_ky)
    r = D(lai_suat_nam) / Decimal(100) * D(chu_ky_ngay) / Decimal(365)
    co_dinh = ngay_tra_thang is not None and 1 <= int(ngay_tra_thang) <= 31
    if co_dinh:
        d = int(ngay_tra_thang)
        ngay1 = date(ngay_nhan.year, ngay_nhan.month,
                     min(d, _cuoi_thang(ngay_nhan.year, ngay_nhan.month)))
        if ngay1 <= ngay_nhan:
            nxt = them_thang(date(ngay_nhan.year, ngay_nhan.month, 1), 1)
            ngay1 = date(nxt.year, nxt.month, min(d, _cuoi_thang(nxt.year, nxt.month)))

        def _ngay_ky(k):
            moc = them_thang(date(ngay1.year, ngay1.month, 1), k - 1)
            return date(moc.year, moc.month, min(d, _cuoi_thang(moc.year, moc.month)))
    rows = []
    du_no = goc
    if phuong_thuc == "TRA_DEU" and r > 0:
        pmt = goc * r / (Decimal(1) - (Decimal(1) + r) ** (-n))
    truoc = ngay_nhan
    for k in range(1, n + 1):
        if co_dinh:
            ngay = _ngay_ky(k)
            so_ngay = max(0, (ngay - truoc).days)
            lai = _r(du_no * D(lai_suat_nam) / Decimal(100) * Decimal(so_ngay) / Decimal(365))
        else:
            ngay = ngay_nhan + timedelta(days=k * int(chu_ky_ngay))
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
        truoc = ngay
    return rows
