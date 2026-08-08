-- 87: Danh mục kê khai vốn & tài sản dài hạn (VCSH / TSCĐ / Nợ dài hạn) — tab Cân đối kế toán
CREATE TABLE IF NOT EXISTS von_muc (
  id BIGSERIAL PRIMARY KEY,
  loai VARCHAR(10) NOT NULL,          -- VCSH | TSCD | NO_DH
  ten VARCHAR(160) NOT NULL,
  so_tien NUMERIC(18,0) DEFAULT 0,    -- VCSH: số vốn · TSCD: giá trị còn lại · NO_DH: dư nợ gốc
  ghi_chu VARCHAR(200)
);
