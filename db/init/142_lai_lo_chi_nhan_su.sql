-- 142: LAI LO RECORD — them CHI PHI NHAN SU luy ke nam (30/09/2026)
--   = bang luong tung thang (chi_phi_dn: tong thu nhap + BH & KPCD phan DN, KE CA bang cho duyet = tam tinh)
--   + thue ngoai DA CHI (thu nhap + khoan khac)
--   + thang chua co bang luong: du phong = tong khoan Chi co dinh co chu "luong" (khong tinh 2 lan)
ALTER TABLE lai_lo_record ADD COLUMN IF NOT EXISTS chi_nhan_su NUMERIC(18,0) DEFAULT 0;
