-- 120: Phieu chi TAM UNG / COC NCC lap tay -> lenh vao Duyet chi Ngan Hang (mot cua duyet chi, CEO 18/09/2026)
-- lenh_chi_bank.phieu_id: lenh sinh tu phieu chi tam ung (khong gan PO / cong no)
ALTER TABLE lenh_chi_bank ADD COLUMN IF NOT EXISTS phieu_id BIGINT REFERENCES phieu_thu_chi(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_lcb_phieu ON lenh_chi_bank(phieu_id);
