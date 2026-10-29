-- 160 — ⭐ KPI lời nhắc việc (Work Reminder — anh Hiếu 29/10/2026): chấm KẾT QUẢ việc đã xong (1–5 sao) bởi người đặt
--       lời nhắc (khi nhắc người khác) hoặc CEO/Admin; vế THỜI GIAN tính tự động từ xong_luc so với hạn (app/kpi_nhac_viec.py).
ALTER TABLE nhac_viec ADD COLUMN IF NOT EXISTS ket_qua_diem    SMALLINT;          -- 1..5 sao
ALTER TABLE nhac_viec ADD COLUMN IF NOT EXISTS ket_qua_ghi_chu TEXT;
ALTER TABLE nhac_viec ADD COLUMN IF NOT EXISTS danh_gia_boi    BIGINT REFERENCES nhan_vien(id) ON DELETE SET NULL;
ALTER TABLE nhac_viec ADD COLUMN IF NOT EXISTS danh_gia_luc    TIMESTAMP;
