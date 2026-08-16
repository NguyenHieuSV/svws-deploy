-- 93: Hóa đơn đầu vào (Cho thuê) — AI đọc email NCC, gắn mã dự án, chờ xác nhận rồi ghi vào chi phí
CREATE TABLE IF NOT EXISTS ct_hoa_don_dau_vao (
  id BIGSERIAL PRIMARY KEY,
  tai_san_id BIGINT REFERENCES tai_san_cho_thue(id) ON DELETE SET NULL,
  ma_du_an VARCHAR(60),
  tu_email VARCHAR(160),
  ncc_ten VARCHAR(200),
  so_hoa_don VARCHAR(60),
  ngay_hd DATE,
  so_tien NUMERIC(18,0) DEFAULT 0,
  mo_ta VARCHAR(300),
  tieu_de VARCHAR(250),
  message_id VARCHAR(250) UNIQUE,
  trang_thai VARCHAR(16) DEFAULT 'CHO_XAC_NHAN',   -- CHO_XAC_NHAN | DA_GHI | BO_QUA
  chi_phi_id BIGINT,
  tao_luc TIMESTAMP
);
