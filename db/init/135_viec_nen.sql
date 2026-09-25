-- 135: Viec chay NEN (AI doc file du toan...) — tra loi ngay, xu ly o luong rieng, luu tien do / ket qua
CREATE TABLE IF NOT EXISTS viec_nen (
  id BIGSERIAL PRIMARY KEY,
  loai VARCHAR(30) NOT NULL,                 -- DTB_NAP_FILE ...
  doi_tuong_id BIGINT,
  ten_file VARCHAR(255),
  trang_thai VARCHAR(12) NOT NULL DEFAULT 'DANG_CHAY',   -- DANG_CHAY | XONG | LOI
  bat_dau TIMESTAMP,
  ket_thuc TIMESTAMP,
  ket_qua JSONB,
  nguoi_dung_id BIGINT
);
CREATE INDEX IF NOT EXISTS idx_viec_nen_dt ON viec_nen(loai, doi_tuong_id);
