-- 134: Tu quet thu hang tuan (AI) — cau hinh + nhat ky cac lan chay (moc trong CSDL: den han thi chay)
CREATE TABLE IF NOT EXISTS cau_hinh_quet_mail (
  id SMALLINT PRIMARY KEY DEFAULT 1,
  bat BOOLEAN NOT NULL DEFAULT TRUE,
  thu SMALLINT NOT NULL DEFAULT 0,        -- 0 = Thu Hai ... 6 = Chu Nhat
  gio SMALLINT NOT NULL DEFAULT 6,        -- gio Viet Nam
  so_ngay SMALLINT NOT NULL DEFAULT 8,    -- quet N ngay gan nhat
  cap_nhat TIMESTAMP
);
INSERT INTO cau_hinh_quet_mail (id) VALUES (1) ON CONFLICT (id) DO NOTHING;
CREATE TABLE IF NOT EXISTS lich_quet_mail (
  id BIGSERIAL PRIMARY KEY,
  nguon VARCHAR(10) NOT NULL DEFAULT 'LICH',    -- LICH | TAY
  bat_dau TIMESTAMP NOT NULL,
  ket_thuc TIMESTAMP,
  trang_thai VARCHAR(12) NOT NULL DEFAULT 'DANG_CHAY',   -- DANG_CHAY | XONG | LOI
  ket_qua JSONB,
  nguoi_dung_id BIGINT
);
