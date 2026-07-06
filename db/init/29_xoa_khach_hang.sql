-- ============================================================
-- SVWS 29 — Nới ràng buộc để XÓA được khách hàng chưa có giao dịch thật
--   • bao_gia_form (báo giá nháp) và email_log không nên chặn xóa khách:
--     đổi sang ON DELETE SET NULL (nháp/log giữ nguyên, chỉ gỡ liên kết).
--   • Các chứng từ thật (bao_gia, don_hang, cong_no, du_an, hop_dong_thue,
--     phieu_thu_chi, tai_san_cho_thue) VẪN chặn xóa — đúng nguyên tắc giữ vết.
-- ============================================================
BEGIN;

ALTER TABLE bao_gia_form DROP CONSTRAINT IF EXISTS bao_gia_form_khach_hang_id_fkey;
ALTER TABLE bao_gia_form ADD CONSTRAINT bao_gia_form_khach_hang_id_fkey
  FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id) ON DELETE SET NULL;

ALTER TABLE email_log DROP CONSTRAINT IF EXISTS email_log_khach_hang_id_fkey;
ALTER TABLE email_log ADD CONSTRAINT email_log_khach_hang_id_fkey
  FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id) ON DELETE SET NULL;

COMMIT;
