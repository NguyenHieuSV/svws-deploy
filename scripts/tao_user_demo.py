"""
Tạo 3 người dùng demo để thử phân quyền (chạy SAU schema + seed_rbac).
  python -m scripts.tao_user_demo
"""
from app.database import SessionLocal
from app.models import NguoiDung, NhanVien, VaiTro
from app.security import bam_mat_khau

DEMO = [
    ("ceo@svws.vn", "CEO", "Giám đốc demo"),
    ("thukho@svws.vn", "THUKHO", "Thủ kho demo"),
    ("nvkd@svws.vn", "NV_KD", "NV Kinh doanh demo"),
    ("nccmua@svws.vn", "NV_MUA", "NV Mua hàng demo"),
    ("tpcu@svws.vn", "TP_CU", "Trưởng P. Cung ứng demo"),
    ("nvda@svws.vn", "NV_DA", "NV Dự án demo"),
    ("tpda@svws.vn", "TP_DA", "Trưởng dự án demo"),
    ("ktt@svws.vn", "KTT", "Kế toán trưởng demo"),
    ("tpkd@svws.vn", "TP_KD", "Trưởng P. Kinh doanh demo"),
    ("nvkt@svws.vn", "NV_KT", "NV Kế toán demo"),
    ("nvhcns@svws.vn", "NV_HCNS", "NV Hành chính-Nhân sự demo"),
    ("nvthue@svws.vn", "NV_THUE", "NV Dịch vụ cho thuê demo"),
    ("nvcrm@svws.vn", "NV_CRM", "NV Chăm sóc KH demo"),
]
MAT_KHAU = "matkhau123"


def main():
    db = SessionLocal()
    try:
        for email, ma_vt, ho_ten in DEMO:
            vt = db.query(VaiTro).filter_by(ma=ma_vt).first()
            if not vt:
                print(f"! Chưa seed vai trò {ma_vt} — chạy SVWS_seed_rbac.sql trước.")
                continue
            nd = db.query(NguoiDung).filter_by(email=email).first()
            if not nd:
                nd = NguoiDung(email=email, vai_tro_id=vt.id,
                               mat_khau_hash=bam_mat_khau(MAT_KHAU), trang_thai="HOAT_DONG")
                db.add(nd); db.flush()
                db.add(NhanVien(nguoi_dung_id=nd.id, ho_ten=ho_ten, chuc_danh=vt.ten,
                               luong_co_ban=15000000, trang_thai='DANG_LAM'))
                print(f"+ Tạo {email} ({ma_vt})")
            else:
                print(f"= Đã có {email}")
        db.commit()
        print(f"\nMật khẩu demo: {MAT_KHAU}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
