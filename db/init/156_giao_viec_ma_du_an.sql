-- 156 — Giao việc có MÃ DỰ ÁN (27/10/2026): chọn từ mã đơn hàng DA / DV / TM… chưa hoàn thành + mã dự án đã đặt tên chưa xong.
-- Nhân viên chọn việc khi báo cáo ngày → «Mã liên quan» của báo cáo tự lấy mã này (nếu chưa chọn mã khác).
ALTER TABLE giao_viec ADD COLUMN IF NOT EXISTS ma_du_an VARCHAR(40);
