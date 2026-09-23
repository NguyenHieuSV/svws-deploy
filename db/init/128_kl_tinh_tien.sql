-- 128: He thong (dong ho) trong Bao cao khoi luong: TINH TIEN (khoi luong x don gia = doanh thu thang) hay chi THAM KHAO
ALTER TABLE ct_bcvh_chi_tieu ADD COLUMN IF NOT EXISTS tinh_tien BOOLEAN DEFAULT TRUE;
