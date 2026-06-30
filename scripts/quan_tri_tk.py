"""
Quản trị tài khoản BẰNG BIẾN MÔI TRƯỜNG (không cần gõ lệnh, chạy tự động khi khởi động).

Đặt các biến trên Render → Environment, rồi Redeploy:

  DEMO_PASSWORD = <mật khẩu mới>     → đổi mật khẩu CHUNG cho mọi tài khoản @svws.vn
                                        (matkhau123 sẽ hết hiệu lực). Nên đặt kèm SEED_DEMO=0.

  ADMIN_EMAIL    = sep@congty.com     ┐  tạo MỚI (hoặc cập nhật) 1 tài khoản
  ADMIN_PASSWORD = <mật khẩu mạnh>    │  quản trị THẬT, vai trò Giám đốc (CEO).
  ADMIN_TEN      = Nguyễn Lê Hiếu     ┘  (ADMIN_TEN tùy chọn)

Chạy được nhiều lần, an toàn (idempotent).
"""
import os

from app.database import SessionLocal
from app.models import NguoiDung, NhanVien, VaiTro
from app.security import bam_mat_khau


def main():
    db = SessionLocal()
    try:
        # 1) Đổi mật khẩu chung cho tài khoản demo @svws.vn
        new_demo = (os.environ.get("DEMO_PASSWORD") or "").strip()
        if new_demo:
            users = db.query(NguoiDung).filter(NguoiDung.email.like("%@svws.vn")).all()
            for u in users:
                u.mat_khau_hash = bam_mat_khau(new_demo)
            print(f"==> Đã đổi mật khẩu {len(users)} tài khoản @svws.vn")

        # 2) Tạo/cập nhật 1 tài khoản quản trị THẬT (vai trò Giám đốc)
        ae = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
        ap = (os.environ.get("ADMIN_PASSWORD") or "").strip()
        if ae and ap:
            vt = db.query(VaiTro).filter_by(ma="CEO").first()
            u = db.query(NguoiDung).filter_by(email=ae).first()
            if u is None:
                u = NguoiDung(email=ae, vai_tro_id=(vt.id if vt else None),
                              mat_khau_hash=bam_mat_khau(ap), trang_thai="HOAT_DONG")
                db.add(u); db.flush()
                db.add(NhanVien(nguoi_dung_id=u.id,
                                ho_ten=(os.environ.get("ADMIN_TEN") or "Quản trị"),
                                chuc_danh=(vt.ten if vt else "Giám đốc"),
                                luong_co_ban=0, trang_thai="DANG_LAM"))
                print(f"==> Đã TẠO tài khoản quản trị {ae}")
            else:
                u.mat_khau_hash = bam_mat_khau(ap)
                if vt:
                    u.vai_tro_id = vt.id
                u.trang_thai = "HOAT_DONG"
                print(f"==> Đã CẬP NHẬT tài khoản quản trị {ae}")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
