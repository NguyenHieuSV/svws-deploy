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
TOI_DA_LUOT = 4                     # mỗi cửa sổ: còn thư mới (con_lai) thì lặp tới chừng này lượt
CUA_SO_NGAY = 7                     # quét theo từng CỬA SỔ 7 ngày (IMAP SINCE … BEFORE …): lấy cả ~1.000 thư 30 ngày kèm đính kèm
                                    # vào bộ nhớ một lần (lượt #63 14:27 06/11/2026 bị cắt — thực ra do deploy PR #29, nhưng
                                    # 52 phút lấy thư vẫn quá lâu); thư đã biết nay chỉ lấy Message-ID (_hdc_mid_da_biet)
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


def _khoi_dong():
    from .nhac_viec_service import gio_hien_tai
    return gio_hien_tai()


KHOI_DONG = _khoi_dong()            # mốc tiến trình này nạp module: lượt bắt đầu TRƯỚC mốc mà không còn luồng = của tiến trình cũ


def dang_chay(db):
    """Lượt đang chạy hoặc None. Dòng DANG_CHAY mà luồng không còn trong tiến trình này (Render khởi động lại / deploy giữa lượt)
    hoặc quá QUA_HAN → đóng là LOI ngay (chưa commit) để không chặn Quét ngay; tránh ghi đè lượt vừa xong đang ghi kết quả."""
    from .models import ViecNen
    from .nhac_viec_service import gio_hien_tai
    bay_gio = gio_hien_tai()
    for v in db.query(ViecNen).filter_by(loai=LOAI, trang_thai="DANG_CHAY").order_by(ViecNen.id.desc()).all():
        t = _luong.get(v.id)
        if t is not None:
            if t.is_alive():
                return v
            continue                                    # luồng vừa xong, đang ghi kết quả → không đụng
        if v.bat_dau and v.bat_dau >= KHOI_DONG and (bay_gio - v.bat_dau) < QUA_HAN:
            return v                                    # lượt của worker khác cùng bản dựng (nếu chạy nhiều worker)
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
    """Cộng dồn các LƯỢT trong một cửa sổ (việc mới làm cộng; trạng thái lặp lại lấy lượt cuối)."""
    for kk, v in (k or {}).items():
        if kk in ("ok", "mau_thu"):
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            tong[kk] = v
        elif kk in _TONG:
            tong[kk] = tong.get(kk, 0) + v
        else:
            tong[kk] = v


def _gop_cua_so(tong: dict, cs: dict):
    """Cộng các CỬA SỔ: mọi số đều cộng (thư mỗi cửa sổ khác nhau); tu_ngay/den_ngay của cửa sổ không ghi đè mốc chung."""
    for kk, v in (cs or {}).items():
        if kk in ("tu_ngay", "den_ngay"):
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            tong[kk] = v
        else:
            tong[kk] = tong.get(kk, 0) + v


def cua_so(moc, hom_nay, buoc: int = CUA_SO_NGAY) -> list:
    """Chia [moc, hôm nay] thành các cửa sổ kín `buoc` ngày [tu, den) + cửa sổ cuối MỞ (den=None: chỉ SINCE, gồm cả hôm nay)."""
    ds, tu = [], moc
    while (hom_nay - tu).days >= buoc:
        ds.append((tu, tu + timedelta(days=buoc)))
        tu += timedelta(days=buoc)
    ds.append((tu, None))
    return ds


def _chay(viec_id: int, nd_id, moc):
    """Luồng nền: quét từng CỬA SỔ 7 ngày từ `moc` tới nay; trong cửa sổ lặp từng lượt tới khi hết thư mới (con_lai = 0) hoặc đủ
    TOI_DA_LUOT; ghi tiến độ + kết quả (cộng dồn) vào viec_nen. Lỗi hộp thư → dừng (các cửa sổ đã xong vẫn giữ)."""
    from fastapi import HTTPException
    from .models import ViecNen, NguoiDung
    from .nhac_viec_service import gio_hien_tai
    from .routers.ke_toan_quy import hdc_quet_lo
    ds_cs = cua_so(moc, gio_hien_tai().date())
    tong, loi = {"tu_ngay": str(moc), "luot": 0, "so_cua_so": len(ds_cs), "cua_so_xong": 0, "cua_so_ngay": CUA_SO_NGAY}, []
    td = {"buoc": "DANG_LAY_THU", "luot": 1, "toi_da_luot": TOI_DA_LUOT, "cua_so": 1, "so_cua_so": len(ds_cs), "da_them_tong": 0}

    def bao(x=None):
        td.update(x or {})
        _ghi_tien_do(viec_id, dict(td))

    db = SessionLocal()
    try:
        nd = db.get(NguoiDung, nd_id) if nd_id else None
        for i_cs, (tu, den) in enumerate(ds_cs, 1):
            tong_cs, dung = {}, False
            for luot in range(1, TOI_DA_LUOT + 1):
                bao({"cua_so": i_cs, "tu": str(tu), "den": (str(den) if den else None), "luot": luot, "buoc": "DANG_LAY_THU",
                     "so_thu": 0, "da_lay": 0, "da_xet": 0, "da_them": 0, "ai": 0, "doc_nhan": 0, "trung": 0, "con_lai": 0,
                     "bo_qua_header": 0, "da_them_tong": tong.get("da_them", 0) + tong_cs.get("da_them", 0)})
                try:
                    k = hdc_quet_lo(db, nd, tu, bao_tien_do=bao, den_ngay=den)
                except HTTPException as e:
                    db.rollback()
                    loi.append(f"Cửa sổ {i_cs} lượt {luot}: {e.detail}")
                    dung = True
                    break
                except Exception as e:
                    db.rollback()
                    loi.append(f"Cửa sổ {i_cs} lượt {luot}: {type(e).__name__}: {str(e)[:150]}")
                    dung = True
                    break
                tong["luot"] += 1
                _gop(tong_cs, k)
                if not k.get("con_lai"):
                    break
            _gop_cua_so(tong, tong_cs)
            if dung:
                break
            tong["cua_so_xong"] = i_cs
    finally:
        db.close()
    print(f"[HDC_QUET_NEN] #{viec_id} xong: cua_so={tong.get('cua_so_xong')}/{tong.get('so_cua_so')} luot={tong.get('luot')} "
          f"thu={tong.get('thu_moi')} them={tong.get('da_them')} con_lai={tong.get('con_lai')} loi={loi}")
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
