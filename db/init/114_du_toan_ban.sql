-- 114: Du toan hang ban — noi MA HANG BAN duoc tao dau tien (truoc bao gia/don hang)
CREATE TABLE IF NOT EXISTS du_toan_ban (
  id BIGSERIAL PRIMARY KEY,
  ma VARCHAR(60) NOT NULL,
  khach_hang VARCHAR(200),
  mo_ta TEXT,
  ngay DATE,
  nguoi_tao VARCHAR(120),
  tao_luc TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS du_toan_ban_muc (
  id BIGSERIAL PRIMARY KEY,
  du_toan_id BIGINT REFERENCES du_toan_ban(id) ON DELETE CASCADE,
  ten VARCHAR(250) NOT NULL,
  quy_cach TEXT,
  don_vi VARCHAR(40),
  so_luong NUMERIC(14,2) DEFAULT 0,
  don_gia NUMERIC(18,0) DEFAULT 0,
  ghi_chu TEXT
);
CREATE INDEX IF NOT EXISTS idx_dtb_muc ON du_toan_ban_muc(du_toan_id);
