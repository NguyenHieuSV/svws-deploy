-- 46_nhac_viec_gui.sql — hạ tầng GỬI TIN cho Work Reminder (Google Chat)
-- (1) đánh dấu lời nhắc đã gửi lúc tạo -> khởi động lại app không gửi trùng
ALTER TABLE nhac_viec ADD COLUMN IF NOT EXISTS da_gui_tao BOOLEAN NOT NULL DEFAULT FALSE;

-- (2) chốt bản tin tổng hợp theo NGÀY: khoá chính là ngày nên hai tiến trình
--     cùng chạy thì chỉ một cái chèn được -> không bao giờ gửi bản tin 2 lần.
CREATE TABLE IF NOT EXISTS nhac_viec_ban_tin (
    ngay      DATE PRIMARY KEY,
    so_nguoi  INT NOT NULL DEFAULT 0,
    so_viec   INT NOT NULL DEFAULT 0,
    ket_qua   TEXT,
    tao_luc   TIMESTAMPTZ NOT NULL DEFAULT now()
);
