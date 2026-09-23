-- 131: Bao gia NCC doc tu EMAIL (AI) — cho xac nhan roi moi vao San pham NCC / ho so NCC
CREATE TABLE IF NOT EXISTS bg_email_cho (
  id BIGSERIAL PRIMARY KEY,
  message_id VARCHAR(250) UNIQUE,
  tu_email VARCHAR(160),
  tieu_de VARCHAR(250),
  ngay_thu DATE,
  nha_cung_cap_id BIGINT REFERENCES nha_cung_cap(id) ON DELETE SET NULL,
  ncc_ai JSONB,
  san_pham JSONB,
  dinh_kem JSONB,
  nguon_doc VARCHAR(40),
  trang_thai VARCHAR(16) DEFAULT 'CHO_XAC_NHAN',   -- CHO_XAC_NHAN | DA_XAC_NHAN | BO_QUA
  ket_qua JSONB,
  tao_luc TIMESTAMP,
  xac_nhan_luc TIMESTAMP,
  nguoi_xac_nhan BIGINT
);
CREATE INDEX IF NOT EXISTS idx_bg_email_cho_tt ON bg_email_cho(trang_thai);
