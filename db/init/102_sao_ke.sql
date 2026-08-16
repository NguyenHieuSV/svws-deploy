-- 102: Sao ke ngan hang + doi soat
CREATE TABLE IF NOT EXISTS sao_ke_bank (
  id BIGSERIAL PRIMARY KEY,
  ten_file VARCHAR(200),
  ngan_hang VARCHAR(60),
  tu_ngay DATE,
  den_ngay DATE,
  so_dong INT DEFAULT 0,
  nguoi_tao BIGINT REFERENCES nguoi_dung(id),
  tao_luc TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sao_ke_dong (
  id BIGSERIAL PRIMARY KEY,
  sao_ke_id BIGINT REFERENCES sao_ke_bank(id) ON DELETE CASCADE,
  ngay DATE,
  dien_giai VARCHAR(400),
  tien_vao NUMERIC(18,0) DEFAULT 0,
  tien_ra NUMERIC(18,0) DEFAULT 0,
  so_du NUMERIC(18,0),
  khop_loai VARCHAR(20),
  khop_id BIGINT,
  khop_mo_ta VARCHAR(300)
);
CREATE INDEX IF NOT EXISTS idx_sao_ke_dong_sk ON sao_ke_dong(sao_ke_id);
