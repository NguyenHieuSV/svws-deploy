-- 138: HOA DON BAN DA GUI KHACH — doc thu gui di (Bcc ve inf@) co hoa don, khop hoa don ban, ghi gui_khach_*;
-- thu chua khop vao hang cho gan tay. Luong hoa don MUA bo qua thu cong ty gui di.
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS gui_khach_luc TIMESTAMP;
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS gui_khach_den VARCHAR(200);
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS gui_khach_nguon VARCHAR(16);   -- EMAIL | TAY
CREATE TABLE IF NOT EXISTS kt_hd_gui_khach (
  id BIGSERIAL PRIMARY KEY,
  message_id VARCHAR(250) UNIQUE,
  tu_email VARCHAR(160),
  den_email VARCHAR(300),
  tieu_de VARCHAR(250),
  ngay_gui DATE,
  so_hoa_don VARCHAR(80),
  so_tien NUMERIC(18,0),
  ten_file VARCHAR(255),
  ai_khach_ten VARCHAR(200),
  khach_hang_id BIGINT REFERENCES khach_hang(id) ON DELETE SET NULL,
  hoa_don_id BIGINT,
  cong_no_id BIGINT,
  trang_thai VARCHAR(16) NOT NULL DEFAULT 'CHUA_KHOP',   -- DA_KHOP | CHUA_KHOP | BO_QUA
  nguoi_xu_ly BIGINT,
  xu_ly_luc TIMESTAMP,
  tao_luc TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_hdgk_tt ON kt_hd_gui_khach(trang_thai);
