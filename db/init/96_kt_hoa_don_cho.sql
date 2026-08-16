-- 96: Hóa đơn MUA từ email (Kế toán) — AI đọc thư NCC, chờ xác nhận rồi mới vào bảng Hóa đơn
CREATE TABLE IF NOT EXISTS kt_hoa_don_cho (
  id BIGSERIAL PRIMARY KEY,
  nha_cung_cap_id BIGINT REFERENCES nha_cung_cap(id) ON DELETE SET NULL,
  tu_email VARCHAR(160),
  ncc_ten VARCHAR(200),
  so_hoa_don VARCHAR(60),
  ngay_hd DATE,
  tien_truoc_thue NUMERIC(18,0) DEFAULT 0,
  thue_suat NUMERIC(5,2) DEFAULT 8,
  tong_tien NUMERIC(18,0) DEFAULT 0,
  mo_ta VARCHAR(300),
  tieu_de VARCHAR(250),
  message_id VARCHAR(250) UNIQUE,
  trang_thai VARCHAR(16) DEFAULT 'CHO_XAC_NHAN',   -- CHO_XAC_NHAN | DA_GHI | BO_QUA
  hoa_don_id BIGINT,
  tao_luc TIMESTAMP
);
