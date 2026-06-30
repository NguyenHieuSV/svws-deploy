-- ============================================================
-- SVWS 21 — Định mức & tiêu hao vật tư/hóa chất theo hệ thống (tài sản) / tháng
-- ============================================================
BEGIN;

CREATE TABLE IF NOT EXISTS dinh_muc_tieu_hao (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tai_san_id BIGINT NOT NULL REFERENCES tai_san_cho_thue(id) ON DELETE CASCADE,
  hang_hoa_id BIGINT NOT NULL REFERENCES hang_hoa(id),
  dinh_muc_thang NUMERIC(15,3) DEFAULT 0,
  ghi_chu VARCHAR(200),
  UNIQUE (tai_san_id, hang_hoa_id)
);

CREATE TABLE IF NOT EXISTS tieu_hao_thuc_te (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tai_san_id BIGINT NOT NULL REFERENCES tai_san_cho_thue(id) ON DELETE CASCADE,
  hang_hoa_id BIGINT NOT NULL REFERENCES hang_hoa(id),
  thang VARCHAR(7) NOT NULL,
  so_luong NUMERIC(15,3) DEFAULT 0,
  don_gia NUMERIC(18,0) DEFAULT 0,
  ngay_ghi DATE DEFAULT current_date,
  nguon VARCHAR(16) DEFAULT 'THU_CONG',
  da_ghi_chi_phi BOOLEAN DEFAULT FALSE,
  ghi_chu VARCHAR(200),
  UNIQUE (tai_san_id, hang_hoa_id, thang)
);
CREATE INDEX IF NOT EXISTS idx_thtt ON tieu_hao_thuc_te(tai_san_id, thang);

-- Seed định mức mẫu cho hệ thống RO (CT-RO-01)
INSERT INTO dinh_muc_tieu_hao (tai_san_id, hang_hoa_id, dinh_muc_thang)
SELECT t.id, h.id, dm.dm FROM (VALUES
  ('CT-RO-01','HC-ANTI',40),('CT-RO-01','HC-CLO',60),('CT-RO-01','HC-PAC',120)
) AS dm(ts_ma,hh_ma,dm)
JOIN tai_san_cho_thue t ON t.ma=dm.ts_ma
JOIN hang_hoa h ON h.ma=dm.hh_ma
WHERE NOT EXISTS (SELECT 1 FROM dinh_muc_tieu_hao d WHERE d.tai_san_id=t.id AND d.hang_hoa_id=h.id);

COMMIT;
