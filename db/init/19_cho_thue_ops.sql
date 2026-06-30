-- ============================================================
-- SVWS 19 — Cho thuê mở rộng: tài sản · chi phí vận hành · bảo trì
-- + gắn đề xuất mua hàng vào "mã bán hàng" của cho thuê (cho_thue_ma).
-- Idempotent.
-- ============================================================
BEGIN;

ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS cho_thue_ma VARCHAR(40);

-- Tài sản cho thuê (mã bán hàng = ma)
CREATE TABLE IF NOT EXISTS tai_san_cho_thue (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ma VARCHAR(40) UNIQUE NOT NULL,
  ten VARCHAR(200) NOT NULL,
  loai VARCHAR(20) DEFAULT 'THIET_BI',          -- THIET_BI / HE_THONG / XE / KHAC
  nguyen_gia NUMERIC(18,0) DEFAULT 0,
  gia_thue_thang NUMERIC(18,0) DEFAULT 0,
  khau_hao_thang NUMERIC(18,0) DEFAULT 0,
  ngay_mua DATE,
  tinh_trang VARCHAR(16) DEFAULT 'SAN_SANG',     -- SAN_SANG / DANG_THUE / BAO_TRI / HONG / THANH_LY
  khach_hang_id BIGINT REFERENCES khach_hang(id),
  vi_tri VARCHAR(120),
  ghi_chu TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Chi phí vận hành (thủ công hoặc đồng bộ từ đề xuất mua qua cho_thue_ma)
CREATE TABLE IF NOT EXISTS chi_phi_van_hanh (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tai_san_id BIGINT REFERENCES tai_san_cho_thue(id) ON DELETE SET NULL,
  ma_ban_hang VARCHAR(40),
  loai_chi_phi VARCHAR(16) DEFAULT 'VAT_TU',     -- VAT_TU / SUA_CHUA / NHAN_CONG / KHAC
  so_tien NUMERIC(18,0) DEFAULT 0,
  ngay DATE DEFAULT current_date,
  yeu_cau_mua_id BIGINT REFERENCES yeu_cau_mua(id) ON DELETE SET NULL,
  mo_ta VARCHAR(300),
  nguon VARCHAR(16) DEFAULT 'THU_CONG'           -- THU_CONG / DE_XUAT_MUA / BAO_TRI
);
CREATE INDEX IF NOT EXISTS idx_cpvh_ts ON chi_phi_van_hanh(tai_san_id);

-- Kế hoạch bảo trì
CREATE TABLE IF NOT EXISTS ke_hoach_bao_tri (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tai_san_id BIGINT REFERENCES tai_san_cho_thue(id) ON DELETE CASCADE,
  ten_cong_viec VARCHAR(200) NOT NULL,
  chu_ky_ngay INT DEFAULT 90,
  ngay_ke_tiep DATE,
  lan_cuoi DATE,
  trang_thai VARCHAR(16) DEFAULT 'KE_HOACH',     -- KE_HOACH / HOAN_THANH
  chi_phi_du_kien NUMERIC(18,0) DEFAULT 0,
  ghi_chu TEXT
);
CREATE INDEX IF NOT EXISTS idx_khbt_ts ON ke_hoach_bao_tri(tai_san_id);

-- Seed vài tài sản mẫu (chỉ khi trống)
INSERT INTO tai_san_cho_thue (ma,ten,loai,nguyen_gia,gia_thue_thang,khau_hao_thang,ngay_mua,tinh_trang,vi_tri)
SELECT * FROM (VALUES
  ('CT-RO-01','Hệ thống RO di động 10 m³/h','HE_THONG',850000000,35000000,7080000,DATE '2024-03-15','DANG_THUE','KCN Sóng Thần'),
  ('CT-MBR-02','Cụm MBR container 200 m³/ngày','HE_THONG',1200000000,48000000,10000000,DATE '2023-11-02','SAN_SANG','Kho SVWS'),
  ('CT-BOM-03','Tổ máy bơm & tủ điện dự phòng','THIET_BI',180000000,6000000,1500000,DATE '2024-08-20','BAO_TRI','Xưởng')
) AS v(ma,ten,loai,nguyen_gia,gia_thue_thang,khau_hao_thang,ngay_mua,tinh_trang,vi_tri)
WHERE NOT EXISTS (SELECT 1 FROM tai_san_cho_thue);

COMMIT;
