-- 139: DU TOAN BAN HANG theo form San pham NCC — dong du toan mang NCC · ma SP · spec · nha san xuat · lien ket san_pham_ncc
ALTER TABLE du_toan_ban_muc ADD COLUMN IF NOT EXISTS nha_cung_cap_id BIGINT REFERENCES nha_cung_cap(id) ON DELETE SET NULL;
ALTER TABLE du_toan_ban_muc ADD COLUMN IF NOT EXISTS ncc_ten VARCHAR(200);
ALTER TABLE du_toan_ban_muc ADD COLUMN IF NOT EXISTS ma_sp VARCHAR(60);
ALTER TABLE du_toan_ban_muc ADD COLUMN IF NOT EXISTS spec TEXT;
ALTER TABLE du_toan_ban_muc ADD COLUMN IF NOT EXISTS nha_san_xuat VARCHAR(150);
ALTER TABLE du_toan_ban_muc ADD COLUMN IF NOT EXISTS san_pham_ncc_id BIGINT;
