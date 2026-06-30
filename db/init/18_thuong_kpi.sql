-- ============================================================
-- SVWS 18 — Gắn KPI vào thưởng lương
-- Thêm cột thuong_kpi vào bang_luong + bảng cấu hình hệ số thưởng theo xếp loại.
-- Idempotent.
-- ============================================================
BEGIN;

ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS thuong_kpi NUMERIC(18,0) DEFAULT 0;

CREATE TABLE IF NOT EXISTS cfg_thuong_kpi (
  id INT PRIMARY KEY DEFAULT 1,
  muc_co_so NUMERIC(18,0) DEFAULT 2000000,   -- mức thưởng cơ sở (loại A = mức × hệ số A)
  hs_a NUMERIC(5,2) DEFAULT 1.50,
  hs_b NUMERIC(5,2) DEFAULT 1.00,
  hs_c NUMERIC(5,2) DEFAULT 0.50,
  hs_d NUMERIC(5,2) DEFAULT 0.00,
  CONSTRAINT cfg_thuong_kpi_single CHECK (id = 1)
);
INSERT INTO cfg_thuong_kpi (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

COMMIT;
