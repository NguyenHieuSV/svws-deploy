-- 168 — 🔒 KHÓA TÀI KHOẢN khi KHÔNG PHẢN HỒI việc được giao (Work Reminder) — anh Hiếu 05/11/2026.
--       Việc do người khác nhắc mà người được nhắc vẫn «Chờ làm» quá N ngày (NHAC_VIEC_KHOA_SAU_NGAY = 2) sau hạn
--       → khóa tài khoản đăng nhập (nguoi_dung.trang_thai = KHOA), KPI THÁNG của người đó = 0, nhắn Google Chat.
--       Mỗi lời nhắc chỉ khóa MỘT lần (UNIQUE nhac_viec_id) → khởi động lại máy chủ không khóa / nhắn trùng.
--       Logic: app/khoa_nhac_viec.py · chạy mỗi ngày từ BAO_CAO_NHAC_GIO (scheduler) hoặc nút ▶ của CEO/Admin.
CREATE TABLE IF NOT EXISTS nhac_viec_khoa (
  id                BIGSERIAL PRIMARY KEY,
  nhac_viec_id      BIGINT NOT NULL UNIQUE REFERENCES nhac_viec(id) ON DELETE CASCADE,
  nhan_vien_id      BIGINT NOT NULL REFERENCES nhan_vien(id) ON DELETE CASCADE,
  nguoi_dung_id     BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,   -- NULL = người đó chưa có tài khoản
  thang             VARCHAR(7) NOT NULL,                                   -- tháng của hạn (YYYY-MM) → KPI tháng này = 0
  han               TIMESTAMP,                                             -- hạn hoàn thành / thời điểm nhắc (giờ VN)
  khoa_luc          TIMESTAMP NOT NULL,                                    -- lúc khóa (giờ VN)
  da_khoa_tai_khoan BOOLEAN NOT NULL DEFAULT FALSE,                        -- TRUE = đã đổi nguoi_dung.trang_thai sang KHOA
  mo_khoa_luc       TIMESTAMP,
  mo_khoa_boi       BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
  chat_da_gui       BOOLEAN NOT NULL DEFAULT FALSE,
  chat_loi          TEXT
);
CREATE INDEX IF NOT EXISTS ix_nhac_viec_khoa_nv_thang ON nhac_viec_khoa (nhan_vien_id, thang);
