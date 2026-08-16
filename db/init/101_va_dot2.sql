-- 101: Va dot 2 — gia von hang hoa + luy ke DA DUYET cua PO
ALTER TABLE hang_hoa ADD COLUMN IF NOT EXISTS gia_von NUMERIC(18,0);
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS da_duyet_tt NUMERIC(18,0);
