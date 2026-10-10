"""
Bỏ bước ĐỀ XUẤT MUA HÀNG (CEO chốt 10/10/2026) — chuyển đổi dữ liệu MỘT LẦN lúc khởi động:
  • đề xuất ĐÃ DUYỆT chưa thành PO → PO CHỜ DUYỆT (cần đủ nhà cung cấp + đơn giá; thiếu → đóng);
  • đề xuất MỚI / CHỜ DUYỆT → đóng (TU_CHOI) kèm ghi chú;
  • dòng dự toán hàng bán / BOQ dự án nối đề xuất → nối PO (dòng của đề xuất đã đóng thì mở lại).
Đánh dấu đã chạy bằng audit_log(bang='yeu_cau_mua', hanh_dong='DONG_MODULE'); lỗi KHÔNG chặn app khởi động.
Bảng yeu_cau_mua / yeu_cau_mua_ct giữ nguyên làm lịch sử (hồ sơ PO vẫn tra được "đề xuất gốc").
"""
import re
from datetime import date
from decimal import Decimal

from .database import SessionLocal
from .models import YeuCauMua, YeuCauMuaCt, DonMua, DonMuaCt, AuditLog, DuToanBanMuc, DuAnDuToan

NGAY = "10/10/2026"
GHI_CHU_DONG = f" | Đóng {NGAY}: bỏ bước đề xuất mua — lập PO trực tiếp từ dự toán / BOQ / cho thuê / kho"
GHI_CHU_THIEU = f" | Đóng {NGAY}: bỏ bước đề xuất mua (thiếu nhà cung cấp hoặc đơn giá) — lập PO trực tiếp từ dự toán"
GHI_CHU_PO = f" | {NGAY}: chuyển thành PO chờ duyệt khi bỏ bước đề xuất mua"
_RE_BOQ = re.compile(r"Đã đề xuất mua #(\d+)")


def _tien(dong):
    """[(so_luong, don_gia, thue_suat)] → (tien_hang, tien_thue) — cùng cách làm tròn với PO lập tay (từng dòng)."""
    th = tt = Decimal(0)
    for sl, g, ts in dong:
        line = (Decimal(str(sl or 0)) * Decimal(str(g or 0))).quantize(Decimal(1))
        th += line
        tt += (line * Decimal(str(ts or 0)) / Decimal(100)).quantize(Decimal(1))
    return th, tt


def chuyen_doi(db) -> dict:
    if db.query(AuditLog).filter_by(bang="yeu_cau_mua", hanh_dong="DONG_MODULE").first() is not None:
        return {"da_chay": True}
    kq = {"po": [], "dong": 0, "thieu": 0, "boq_noi": 0, "dtb_noi": 0}
    boq_co_nhan = db.query(DuAnDuToan).filter(DuAnDuToan.ghi_chu.like("%Đã đề xuất mua #%")).all()
    for y in (db.query(YeuCauMua).filter(YeuCauMua.trang_thai == "DA_DUYET", YeuCauMua.don_mua_id.is_(None))
              .order_by(YeuCauMua.id).all()):
        cts = db.query(YeuCauMuaCt).filter_by(yeu_cau_mua_id=y.id).order_by(YeuCauMuaCt.id).all()
        dong = ([(c.hang_hoa_id, c.so_luong, c.don_gia, c.thue_suat or 0) for c in cts]
                or [(y.hang_hoa_id, y.so_luong, y.don_gia, 0)])
        ncc = y.nha_cung_cap_id or next((c.nha_cung_cap_id for c in cts if c.nha_cung_cap_id), None)
        if not ncc or any(g is None or Decimal(str(g)) <= 0 for _h, _s, g, _t in dong):
            y.trang_thai = "TU_CHOI"
            y.ghi_chu = (y.ghi_chu or "") + GHI_CHU_THIEU
            kq["thieu"] += 1
            continue
        th, tt = _tien([(s, g, t) for _h, s, g, t in dong])
        ma = (y.ma_ban or "").strip()[:40] or None
        if not y.don_hang_id and not ma:
            ma = "KHO"
        dm = DonMua(so=None, nha_cung_cap_id=ncc, don_hang_id=y.don_hang_id, ma_ban=ma, vuot_du_toan=y.vuot_du_toan,
                    ngay=date.today(), ngay_hen_giao=y.ngay_can, tien_hang=th, tien_thue=tt, tong_tien=th + tt,
                    trang_thai="CHO_DUYET")
        db.add(dm); db.flush()
        dm.so = f"PO-{date.today():%Y%m%d}-{dm.id}"
        for h, s_, g, t in dong:
            db.add(DonMuaCt(don_mua_id=dm.id, hang_hoa_id=h, so_luong=s_, don_gia=g, thue_suat=t))
        y.trang_thai = "DA_TAO_PO"
        y.don_mua_id = dm.id
        y.ghi_chu = (y.ghi_chu or "") + GHI_CHU_PO
        db.add(AuditLog(nguoi_dung_id=None, hanh_dong="TAO", bang="don_mua", ban_ghi_id=dm.id,
                        gia_tri_moi={"tu_yeu_cau_mua": y.id, "trang_thai": "CHO_DUYET",
                                     "tong_tien": float(th + tt), "ly_do": f"bỏ bước đề xuất mua {NGAY}"}))
        for m in db.query(DuToanBanMuc).filter_by(yeu_cau_mua_id=y.id).all():
            if m.don_mua_id is None:
                m.don_mua_id = dm.id
                kq["dtb_noi"] += 1
        for x in boq_co_nhan:
            if x.don_mua_id is None and re.search(rf"Đã đề xuất mua #{y.id}(?!\d)", x.ghi_chu or ""):
                x.don_mua_id = dm.id
                x.ghi_chu = (_RE_BOQ.sub(f"Đã tạo PO {dm.so}", x.ghi_chu or "") or None)
                kq["boq_noi"] += 1
        kq["po"].append({"yeu_cau_mua": y.id, "po": dm.so, "tong": float(th + tt)})
    for y in db.query(YeuCauMua).filter(YeuCauMua.trang_thai.in_(["MOI", "CHO_DUYET"])).all():
        y.trang_thai = "TU_CHOI"
        y.ghi_chu = (y.ghi_chu or "") + GHI_CHU_DONG
        kq["dong"] += 1
    # dòng BOQ còn mang nhãn đề xuất mà không có PO → gỡ nhãn (dòng mở lại cho 🛒 Tạo PO)
    for x in boq_co_nhan:
        if x.don_mua_id is None and _RE_BOQ.search(x.ghi_chu or ""):
            x.ghi_chu = re.sub(r"( · )?Đã đề xuất mua #\d+", "", x.ghi_chu or "").strip(" ·") or None
    db.add(AuditLog(nguoi_dung_id=None, hanh_dong="DONG_MODULE", bang="yeu_cau_mua", ban_ghi_id=None,
                    gia_tri_moi={"ngay": "2026-10-10", **kq}))
    db.commit()
    return kq


def chay_mot_lan() -> None:
    db = SessionLocal()
    try:
        kq = chuyen_doi(db)
        print(f"[BO_DE_XUAT] {kq}")
    except Exception as e:                      # không để lỗi chuyển đổi chặn app khởi động
        db.rollback()
        print(f"[BO_DE_XUAT] lỗi: {type(e).__name__}: {e}")
    finally:
        db.close()
