-- ============================================================
-- SVWS 28 — Cho phép XÓA tài khoản người dùng
--   Trước đây audit_log.nguoi_dung_id và nhan_vien.nguoi_dung_id
--   chặn xóa (NO ACTION). Đổi thành ON DELETE SET NULL:
--   xóa tài khoản -> nhật ký audit và hồ sơ nhân viên GIỮ NGUYÊN,
--   chỉ gỡ liên kết tới tài khoản đã xóa.
-- ============================================================
BEGIN;

ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS audit_log_nguoi_dung_id_fkey;
ALTER TABLE audit_log ADD CONSTRAINT audit_log_nguoi_dung_id_fkey
  FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(id) ON DELETE SET NULL;

ALTER TABLE nhan_vien DROP CONSTRAINT IF EXISTS nhan_vien_nguoi_dung_id_fkey;
ALTER TABLE nhan_vien ADD CONSTRAINT nhan_vien_nguoi_dung_id_fkey
  FOREIGN KEY (nguoi_dung_id) REFERENCES nguoi_dung(id) ON DELETE SET NULL;

COMMIT;
