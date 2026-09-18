"""💵 ĐÃ TẠM ỨNG MUA HÀNG — tiền ĐÃ TRẢ TRƯỚC cho nhà cung cấp mà CHƯA nhận hàng và CHƯA có hóa đơn.

Một nguồn tính dùng chung cho thẻ trên Overall Financial và danh mục chi tiết:
  ① PO đã trả tiền (một phần hoặc toàn bộ) nhưng trạng thái nhận = CHƯA và chưa có số hóa đơn
     (PO không ghi số HĐ, công nợ của PO chưa gắn hóa đơn mua / số chứng từ).
     Tiền đã trả = «Đã thanh toán» trên công nợ của PO (chỉ ghi khi ngân hàng/quỹ CHI THẬT);
     PO cũ chưa có công nợ → lấy lũy kế đã duyệt chi (da_duyet_tt), không có thì de_nghi_tt.
  ② Phiếu chi TẠM ỨNG cho NCC (không gắn PO) đã duyệt, phần CHƯA cấn trừ.
Hai nhóm không trùng nhau: phiếu chi tạm ứng không gắn công nợ PO.
"""
from decimal import Decimal
from sqlalchemy.orm import Session

from .models import CongNo, DonHang, DonMua, DonMuaCt, HangHoa, NhaCungCap, PhieuThuChi, ThanhToan


def _f(v) -> float:
    return float(v or 0)


def tam_ung_mua_hang(db: Session) -> dict:
    from .nhac_viec_service import gio_hien_tai
    hom_nay = gio_hien_tai().date()

    pos = (db.query(DonMua)
           .filter(DonMua.trang_thai != "TU_CHOI")
           .filter((DonMua.trang_thai_nhan == "CHUA") | (DonMua.trang_thai_nhan.is_(None)))
           .order_by(DonMua.id.desc()).all())
    ids = [p.id for p in pos]
    cn_map: dict[int, list] = {}
    if ids:
        for c in db.query(CongNo).filter(CongNo.don_mua_id.in_(ids)).all():
            cn_map.setdefault(c.don_mua_id, []).append(c)

    rows = []
    for dm in pos:
        cns = cn_map.get(dm.id) or []
        if cns:
            da_tra = sum(_f(c.da_thanh_toan) for c in cns)
        else:   # PO cũ chưa có công nợ: số đã duyệt chi, không có thì số đã ghi trả
            da_tra = _f(dm.da_duyet_tt if dm.da_duyet_tt is not None else dm.de_nghi_tt)
        if da_tra <= 0:
            continue
        co_hd = bool((dm.so_hoa_don or "").strip()) or any(
            c.hoa_don_id is not None or (c.so_ct or "").strip() for c in cns)
        if co_hd:
            continue
        rows.append((dm, cns, da_tra))

    # tên NCC · mã · hàng hóa · ngày trả gần nhất — nạp một lượt
    ncc_ids = {dm.nha_cung_cap_id for dm, _, _ in rows if dm.nha_cung_cap_id}
    ncc_ten = ({n.id: n.ten for n in db.query(NhaCungCap).filter(NhaCungCap.id.in_(ncc_ids)).all()}
               if ncc_ids else {})
    dh_ids = {dm.don_hang_id for dm, _, _ in rows if dm.don_hang_id}
    dh_so = ({d.id: d.so for d in db.query(DonHang).filter(DonHang.id.in_(dh_ids)).all()}
             if dh_ids else {})
    po_ids = [dm.id for dm, _, _ in rows]
    hh_ten: dict[int, list] = {}
    if po_ids:
        for dmid, ten in (db.query(DonMuaCt.don_mua_id, HangHoa.ten)
                          .join(HangHoa, DonMuaCt.hang_hoa_id == HangHoa.id)
                          .filter(DonMuaCt.don_mua_id.in_(po_ids)).order_by(DonMuaCt.id).all()):
            hh_ten.setdefault(dmid, []).append(ten or "")
    cn_ids = [c.id for _, cns, _ in rows for c in cns]
    tt_cuoi: dict[int, object] = {}
    if cn_ids:
        for t in db.query(ThanhToan).filter(ThanhToan.cong_no_id.in_(cn_ids)).all():
            if t.ngay and (t.cong_no_id not in tt_cuoi or t.ngay > tt_cuoi[t.cong_no_id]):
                tt_cuoi[t.cong_no_id] = t.ngay

    po_out = []
    for dm, cns, da_tra in rows:
        ds_ngay = [tt_cuoi[c.id] for c in cns if c.id in tt_cuoi]
        ngay_tra = max(ds_ngay) if ds_ngay else (dm.ngay_tt or dm.ngay_tt_du)
        tong = _f(dm.tong_tien)
        tens = hh_ten.get(dm.id) or []
        po_out.append({
            "id": dm.id, "so": dm.so or f"PO-{dm.id}", "ngay": str(dm.ngay or "")[:10],
            "ncc_ten": ncc_ten.get(dm.nha_cung_cap_id),
            "ma": dh_so.get(dm.don_hang_id) or (dm.ma_ban or None),
            "hang_hoa": (" · ".join(tens[:2]) + (f" +{len(tens) - 2} mặt hàng nữa" if len(tens) > 2 else ""))
                        if tens else None,
            "tong_po": tong, "da_tra": da_tra,
            "ty_le": round(da_tra / tong * 100, 1) if tong > 0 else None,
            "tra_du": bool(tong > 0 and da_tra >= tong),
            "ngay_tra": str(ngay_tra) if ngay_tra else None,
            "so_ngay_cho": (hom_nay - ngay_tra).days if ngay_tra else None,
            "ngay_hen_giao": str(dm.ngay_hen_giao) if dm.ngay_hen_giao else None,
            "tre_giao": bool(dm.ngay_hen_giao and dm.ngay_hen_giao < hom_nay),
            "co_cong_no": bool(cns),
        })
    po_out.sort(key=lambda r: -r["da_tra"])

    # ② phiếu chi tạm ứng NCC đã duyệt, phần chưa cấn trừ
    phieu_out = []
    for p in (db.query(PhieuThuChi)
              .filter(PhieuThuChi.loai == "CHI", PhieuThuChi.la_tam_ung.is_(True),
                      PhieuThuChi.trang_thai == "DA_DUYET",
                      PhieuThuChi.so_tien > PhieuThuChi.da_can_tru)
              .order_by(PhieuThuChi.id.desc()).all()):
        ncc = db.get(NhaCungCap, p.nha_cung_cap_id) if p.nha_cung_cap_id else None
        dh = db.get(DonHang, p.don_hang_id) if getattr(p, "don_hang_id", None) else None
        con = _f(p.so_tien) - _f(p.da_can_tru)
        phieu_out.append({
            "id": p.id, "so": getattr(p, "so", None) or f"PC-{p.id}", "ngay": str(p.ngay or "")[:10],
            "ncc_ten": ncc.ten if ncc else None, "ma": dh.so if dh else None,
            "dien_giai": p.dien_giai,
            "so_tien": _f(p.so_tien), "da_can_tru": _f(p.da_can_tru), "con_treo": con,
            "so_ngay_cho": (hom_nay - p.ngay).days if p.ngay else None,
        })

    tong_po = sum(r["da_tra"] for r in po_out)
    tong_phieu = sum(r["con_treo"] for r in phieu_out)
    return {"tong": tong_po + tong_phieu, "tong_po": tong_po, "tong_phieu": tong_phieu,
            "so_po": len(po_out), "so_phieu": len(phieu_out),
            "so_tre_giao": sum(1 for r in po_out if r["tre_giao"]),
            "po": po_out, "phieu": phieu_out}
