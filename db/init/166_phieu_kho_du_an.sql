-- 166 — 📦 Vật tư theo HẠNG MỤC dự án (anh Hiếu 01/11/2026, phần B): phiếu kho gắn DỰ ÁN và từng dòng phiếu
--       gắn DÒNG DỰ TOÁN BOQ (du_an_du_toan) → đối chiếu định mức (kế hoạch) ↔ thực cấp tại công trường.
ALTER TABLE phieu_kho    ADD COLUMN IF NOT EXISTS du_an_id         BIGINT REFERENCES du_an(id) ON DELETE SET NULL;
ALTER TABLE phieu_kho_ct ADD COLUMN IF NOT EXISTS du_an_du_toan_id BIGINT REFERENCES du_an_du_toan(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_phieu_kho_da    ON phieu_kho(du_an_id);
CREATE INDEX IF NOT EXISTS idx_phieu_kho_ct_dt ON phieu_kho_ct(du_an_du_toan_id);
