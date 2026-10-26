-- 155 — Giao việc (Working time & Report, 26/10/2026): CHỈ CEO nhập / sửa Người nhận việc, Tên công việc, Ngày bắt đầu, Ngày kết thúc.
-- Nhân viên thấy việc được giao trong form «Báo cáo công việc của tôi» và chọn việc khi báo cáo (không sửa được).
-- bao_cao_ngay giữ BẢN CHỤP 4 trường (mig 154) + giao_viec_id trỏ về việc gốc.
CREATE TABLE IF NOT EXISTS giao_viec (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nhan_vien_id BIGINT NOT NULL REFERENCES nhan_vien(id) ON DELETE CASCADE,   -- người nhận việc
  email VARCHAR(150),
  ten_cong_viec VARCHAR(250) NOT NULL,
  bat_dau DATE,
  ket_thuc DATE,
  nguoi_giao BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
  tao_luc TIMESTAMP,
  cap_nhat_luc TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_giao_viec_nv ON giao_viec (nhan_vien_id);
ALTER TABLE bao_cao_ngay ADD COLUMN IF NOT EXISTS giao_viec_id BIGINT REFERENCES giao_viec(id) ON DELETE SET NULL;
