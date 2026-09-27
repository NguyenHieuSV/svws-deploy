-- 136: NHAN SU THUE NGOAI — ca nhan khong ky HDLD (dich vu / khoan viec / CTV / thoi vu / ho kinh doanh)
-- Thue TNCN khau tru tai nguon theo thue suat toan phan (TT 111/2013 Dieu 25.1.i: 10% tu 2.000.000 d/lan;
-- khong cu tru 20%); ho so phap ly; canh bao tuan thu; but toan; tong hop ke khai 05/KK-TNCN.
CREATE TABLE IF NOT EXISTS nhan_su_thue_ngoai (
  id BIGSERIAL PRIMARY KEY,
  ma VARCHAR(20),
  ho_ten VARCHAR(120) NOT NULL,
  ngay_sinh DATE,
  cccd VARCHAR(20),
  cccd_ngay_cap DATE,
  cccd_noi_cap VARCHAR(120),
  dia_chi VARCHAR(255),
  dien_thoai VARCHAR(30),
  email VARCHAR(120),
  ma_so_thue VARCHAR(20),
  cu_tru BOOLEAN NOT NULL DEFAULT TRUE,
  loai_hop_dong VARCHAR(16) NOT NULL DEFAULT 'DICH_VU',   -- DICH_VU | KHOAN_VIEC | CTV | THOI_VU | HO_KINH_DOANH
  so_hop_dong VARCHAR(60),
  ngay_ky DATE,
  ngay_bat_dau DATE,
  ngay_ket_thuc DATE,
  noi_dung_cv TEXT,
  don_gia NUMERIC(18,0) NOT NULL DEFAULT 0,
  don_vi VARCHAR(30),                                       -- thang | ngay | gio | khoan | san pham
  ngan_hang VARCHAR(80),
  so_tai_khoan VARCHAR(30),
  chu_tai_khoan VARCHAR(120),
  cam_ket_08 BOOLEAN NOT NULL DEFAULT FALSE,               -- da nop cam ket 08/CK-TNCN (TT 80/2021)
  cam_ket_ngay DATE,
  hkd_hoa_don BOOLEAN NOT NULL DEFAULT FALSE,              -- ho kinh doanh xuat hoa don (DN khong khau tru)
  tk_chi_phi VARCHAR(10) NOT NULL DEFAULT '642',
  ho_so JSONB NOT NULL DEFAULT '{}'::jsonb,                -- checklist: {hop_dong:true, cccd:true, mst:..., cam_ket:..., hoa_don:...}
  trang_thai VARCHAR(16) NOT NULL DEFAULT 'DANG_HOP_TAC',  -- DANG_HOP_TAC | KET_THUC
  ghi_chu TEXT,
  nguoi_tao BIGINT,
  tao_luc TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nstn_tt ON nhan_su_thue_ngoai(trang_thai);

CREATE TABLE IF NOT EXISTS thanh_toan_thue_ngoai (
  id BIGSERIAL PRIMARY KEY,
  thue_ngoai_id BIGINT NOT NULL REFERENCES nhan_su_thue_ngoai(id) ON DELETE CASCADE,
  ky VARCHAR(7) NOT NULL,                                   -- YYYY-MM (ky ke khai)
  ngay DATE NOT NULL DEFAULT CURRENT_DATE,
  noi_dung VARCHAR(255),
  khoi_luong NUMERIC(12,2) NOT NULL DEFAULT 1,
  don_gia NUMERIC(18,0) NOT NULL DEFAULT 0,
  thu_nhap NUMERIC(18,0) NOT NULL DEFAULT 0,               -- tong thu nhap truoc thue (khoi_luong x don_gia + khac)
  khoan_khac NUMERIC(18,0) NOT NULL DEFAULT 0,
  thue_suat NUMERIC(6,4) NOT NULL DEFAULT 0,               -- 0 | 0.10 | 0.20
  ly_do_thue VARCHAR(160),
  thue_tncn NUMERIC(18,0) NOT NULL DEFAULT 0,
  thuc_nhan NUMERIC(18,0) NOT NULL DEFAULT 0,
  hinh_thuc VARCHAR(4) NOT NULL DEFAULT 'CK',              -- CK | TM
  so_chung_tu VARCHAR(60),
  bien_ban_nghiem_thu BOOLEAN NOT NULL DEFAULT FALSE,
  chung_tu_khau_tru VARCHAR(60),                            -- so chung tu khau tru thue TNCN dien tu da cap
  so_hoa_don VARCHAR(60),                                   -- hoa don cua ho kinh doanh (neu co)
  canh_bao JSONB NOT NULL DEFAULT '[]'::jsonb,
  trang_thai VARCHAR(12) NOT NULL DEFAULT 'NHAP',          -- NHAP | DA_DUYET | DA_CHI
  nguoi_tao BIGINT,
  nguoi_duyet BIGINT,
  ngay_duyet DATE,
  ngay_chi DATE,
  ghi_chu TEXT,
  tao_luc TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tttn_ky ON thanh_toan_thue_ngoai(ky);
CREATE INDEX IF NOT EXISTS idx_tttn_ng ON thanh_toan_thue_ngoai(thue_ngoai_id);

ALTER TABLE tham_so_luong ADD COLUMN IF NOT EXISTS tn_nguong_khau_tru NUMERIC(18,0) NOT NULL DEFAULT 2000000;
ALTER TABLE tham_so_luong ADD COLUMN IF NOT EXISTS tn_tl_thue_cu_tru NUMERIC(6,4) NOT NULL DEFAULT 0.10;
ALTER TABLE tham_so_luong ADD COLUMN IF NOT EXISTS tn_tl_thue_khong_cu_tru NUMERIC(6,4) NOT NULL DEFAULT 0.20;
ALTER TABLE tham_so_luong ADD COLUMN IF NOT EXISTS tn_nguong_khong_tien_mat NUMERIC(18,0) NOT NULL DEFAULT 5000000;
