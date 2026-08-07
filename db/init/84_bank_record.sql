-- 84: Bank record — sổ phát sinh thu/chi qua ngân hàng do CEO tự cập nhật (Overall Financial)
CREATE TABLE IF NOT EXISTS bank_record (
  id BIGSERIAL PRIMARY KEY,
  ngay DATE DEFAULT CURRENT_DATE,
  loai VARCHAR(4) DEFAULT 'CHI',          -- THU | CHI
  ngan_hang VARCHAR(60),
  dien_giai VARCHAR(300),
  ma_ban VARCHAR(60),
  so_tien NUMERIC(18,0) DEFAULT 0,
  nguoi_tao BIGINT REFERENCES nguoi_dung(id),
  tao_luc TIMESTAMP
);
