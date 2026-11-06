"""⏳ QUÉT HÓA ĐƠN MUA TỪ EMAIL Ở LUỒNG NỀN (06/11/2026) — nút «Quét ngay» / «Quét lịch sử» ở Kế toán › Hóa đơn.
Trước đây POST /ke-toan/hoa-don-cho/quet chạy ĐỒNG BỘ trong request: mốc 30 ngày ≈ 1.000 thư IMAP + gọi AI nên Render
cắt kết nối (502) sau ~100 giây dù máy chủ vẫn chạy tiếp và commit; quét 1 ngày cũng mất ~45 giây.
Nay: tạo một dòng viec_nen (loai HDC_QUET_MAIL — bảng việc nền mig 135, không cần migration) → trả {id} ngay; luồng riêng
với session CSDL riêng gọi bộ quét cũ (routers.ke_toan_quy.hdc_quet_lo) từng LƯỢT (mỗi lượt tối đa 25 thư mới; còn thư thì
tự lặp tới TOI_DA_LUOT lượt như quet_mail_service._lap), ghi tiến độ vào viec_nen.ket_qua["tien_do"] để giao diện hỏi
5 giây/lần. Một lượt tại một thời điểm: đang chạy thì trả lượt đó. Endpoint cũ /hoa-don-cho/quet giữ nguyên cho tương thích."""
import threading
from datetime import timedelta

from .database import SessionLocal

LOAI = "HDC_QUET_MAIL"
TOI_DA_LUOT = 4
QUA_HAN = timedelta(hours=2)        # dòng DANG_CHAY cũ hơn mức này = máy chủ đã khởi động lại giữa lượt → đóng là LỖI
GAN_DAY = timedelta(hours=3)        # kết quả lượt gần nhất còn hiện trên bảng trong khoảng này
_khoa = threading.Lock()            # tạo lượt tuần tự (hai người bấm cùng lúc chỉ ra một lượt)
_luong: dict[int, threading.Thread] = {}   # id → luồng (test chờ xong)
# cộng dồn qua các lượt = việc MỚI làm ở từng lượt; khóa khác (thu_moi, trung_bo_qua, khong_khop, con_lai…) là trạng thái
# lặp lại mỗi lượt → lấy giá trị lượt cuối (giống quet_mail_service._gop)
_TONG = ("da_them", "ai", "doc_nhan", "hd_ban", "trung_hd", "sua_cu")


def to_dict(v) -> dict:
    """Dạng trả cho giao diện: tiến độ tách khỏi kết quả; gan_day = vừa xong trong GAN_DAY (bảng còn hiện dòng kết quả)."""
    from .nhac_viec_service import gio_hien_tai
    kq = dict(v.ket_qua or {})
    td = kq.pop("tien_do", None) or {}
    return {"id": v.id, "trang_thai": v.trang_thai, "dang_chay": v.trang_thai == "DANG_CHAY",
            "bat_dau": str(v.bat_dau)[:16] if v.bat_dau else None,
            "ket_thuc": str(v.ket_thuc)[:16] if v.ket_thuc else None,
            "gan_day": bool(v.ket_thuc and (gio_hien_tai() - v.ket_thuc) < GAN_DAY),
            "tu_ngay": kq.get("tu_ngay"), "tien_do": td, "ket_qua": kq, "nguoi_dung_id": v.nguoi_dung_id}


def dang_chay(db):
    """Lượt đang chạy (chưa quá hạn) hoặc None. Dòng DANG_CHAY kẹt từ lần máy chủ khởi động lại → đóng là LOI (chưa commit)."""
    from .models import ViecNen
    from .nhac_viec_service import gio_hien_tai
    bay_gio = gio_hien_tai()
    for v in db.query(ViecNen).filter_by(loai=LOAI, trang_thai="DANG_CHAY").order_by(ViecNen.id.desc()).all():
        if v.bat_dau and (bay_gio - v.bat_dau) < QUA_HAN:
            return v
        v.trang_thai, v.ket_thuc = "LOI", bay_gio
        v.ket_qua = dict(v.ket_qua or {},
                         loi=["Lượt quét bị cắt giữa chừng (máy chủ khởi động lại) — bấm Quét ngay để chạy lại"])
    return None


def moi_nhat(db):
    """Lượt gần nhất (đang chạy / xong / lỗi) — None nếu chưa từng quét nền."""
    from .models import ViecNen
    dang_chay(db)
    db.commit()
    return db.query(ViecNen).filter_by(loai=LOAI).order_by(ViecNen.id.desc()).first()


def bat_dau(db, nd, moc):
    """Tạo lượt quét nền từ mốc `moc` (date) → (viec, moi). Đang có lượt chạy → trả lượt đó, moi=False. Đã commit."""
    from .models import ViecNen
    from .nhac_viec_service import gio_hien_tai
    with _khoa:
        dc = dang_chay(db)
        if dc is not None:
            db.commit()
            return dc, False
        v = ViecNen(loai=LOAI, ten_file=f"từ {moc}", trang_thai="DANG_CHAY", bat_dau=gio_hien_tai(),
                    nguoi_dung_id=(nd.id if nd is not None else None),
                    ket_qua={"tu_ngay": str(moc), "tien_do": {"buoc": "CHO", "luot": 1, "toi_da_luot": TOI_DA_LUOT}})
        db.add(v)
        db.commit()
        vid = v.id
        t = threading.Thread(target=_chay, args=(vid, v.nguoi_dung_id, moc), name=f"svws-hdc-quet-{vid}", daemon=True)
        _luong[vid] = t
        t.start()
        return v, True


def cho_xong(viec_id: int, timeout: float = 60) -> bool:
    """Chờ luồng của lượt `viec_id` kết thúc (dùng cho test). True nếu đã xong."""
    t = _luong.get(viec_id)
    if t is None:
        return True
    t.join(timeout)
    return not t.is_alive()


def _ghi_tien_do(viec_id: int, td: dict):
    """Ghi tiến độ bằng session RIÊNG — giao dịch quét vẫn một commit cuối lượt như cũ."""
    from .models import ViecNen
    db = SessionLocal()
    try:
        v = db.get(ViecNen, viec_id)
        if v is not None:
            v.ket_qua = dict(v.ket_qua or {}, tien_do=td)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _gop(tong: dict, k: dict):
    for kk, v in (k or {}).items():
        if kk in ("ok", "mau_thu"):
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            tong[kk] = v
        elif kk in _TONG:
            tong[kk] = tong.get(kk, 0) + v
        else:
            tong[kk] = v


def _chay(viec_id: int, nd_id, moc):
    """Luồng nền: quét từng lượt tới khi hết thư mới (con_lai = 0) hoặc đủ TOI_DA_LUOT; ghi tiến độ + kết quả vào viec_nen."""
    from fastapi import HTTPException
    from .models import ViecNen, NguoiDung
    from .nhac_viec_service import gio_hien_tai
    from .routers.ke_toan_quy import hdc_quet_lo
    tong, loi = {"tu_ngay": str(moc), "luot": 0}, []
    td = {"buoc": "DANG_LAY_THU", "luot": 1, "toi_da_luot": TOI_DA_LUOT}

    def bao(x=None):
        td.update(x or {})
        _ghi_tien_do(viec_id, dict(td))

    db = SessionLocal()
    try:
        nd = db.get(NguoiDung, nd_id) if nd_id else None
        for luot in range(1, TOI_DA_LUOT + 1):
            bao({"luot": luot, "buoc": "DANG_LAY_THU"})
            try:
                k = hdc_quet_lo(db, nd, moc, bao_tien_do=bao)
            except HTTPException as e:
                db.rollback()
                loi.append(f"Lượt {luot}: {e.detail}")
                break
            except Exception as e:
                db.rollback()
                loi.append(f"Lượt {luot}: {type(e).__name__}: {str(e)[:150]}")
                break
            tong["luot"] = luot
            _gop(tong, k)
            if not k.get("con_lai"):
                break
    finally:
        db.close()
    print(f"[HDC_QUET_NEN] #{viec_id} xong: luot={tong.get('luot')} thu={tong.get('thu_moi')} them={tong.get('da_them')} "
          f"con_lai={tong.get('con_lai')} loi={loi}")
    db2 = SessionLocal()
    try:
        v = db2.get(ViecNen, viec_id)
        if v is not None:
            v.ket_thuc = gio_hien_tai()
            v.trang_thai = "LOI" if (loi and not tong["luot"]) else "XONG"     # lượt đầu đã hỏng = LỖI; có lượt xong = XONG (kèm loi)
            v.ket_qua = {**tong, "loi": loi, "tien_do": {**td, "buoc": "XONG"}}
            db2.commit()
    except Exception as e:
        db2.rollback()
        print(f"[HDC_QUET_NEN] #{viec_id} không ghi được kết quả: {type(e).__name__}: {e}")
    finally:
        db2.close()
        _luong.pop(viec_id, None)
