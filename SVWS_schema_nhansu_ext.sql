-- ============ NHÂN SỰ & LƯƠNG — mở rộng hồ sơ lương + kỳ lương + OT + BH DN ============
-- Hồ sơ lương trên nhân viên
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS luong_dong_bh        NUMERIC(18,0) NOT NULL DEFAULT 0; -- lương đóng BH (0 = dùng lương cơ bản)
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS so_phu_thuoc         INT           NOT NULL DEFAULT 0;
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS phu_cap_an           NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS phu_cap_di_lai       NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS phu_cap_dien_thoai   NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS phu_cap_trach_nhiem  NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS ma_so_thue           VARCHAR(20);
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS so_tai_khoan         VARCHAR(30);
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS ngan_hang            VARCHAR(80);
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS email                VARCHAR(120);
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS tk_chi_phi           VARCHAR(10)   NOT NULL DEFAULT '642';

-- Bảng lương (1 dòng / nhân viên / tháng) — bổ sung công, OT, BH DN, chi phí DN, email
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS cong_chuan        NUMERIC(5,1)  NOT NULL DEFAULT 26;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS cong_thuc_te      NUMERIC(5,1)  NOT NULL DEFAULT 26;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS gio_ot_thuong     NUMERIC(6,1)  NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS gio_ot_cuoi_tuan  NUMERIC(6,1)  NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS gio_ot_le         NUMERIC(6,1)  NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS luong_thuc_te     NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS tam_ung           NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS thu_nhap_chiu_thue NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS bhxh_dn           NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS bhyt_dn           NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS bhtn_dn           NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS chi_phi_dn        NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS email_sent        BOOLEAN       NOT NULL DEFAULT FALSE;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS ngay_gui_email    TIMESTAMP;

-- Kỳ lương (header theo tháng)
CREATE TABLE IF NOT EXISTS ky_luong (
    thang        VARCHAR(7) PRIMARY KEY,          -- 'YYYY-MM'
    cong_chuan   NUMERIC(5,1)  NOT NULL DEFAULT 26,
    ngay_chot    DATE,                            -- chậm nhất ngày 7
    trang_thai   VARCHAR(20)   NOT NULL DEFAULT 'NHAP',   -- NHAP / DA_CHOT
    da_gui_email BOOLEAN       NOT NULL DEFAULT FALSE,
    tong_thu_nhap  NUMERIC(18,0) NOT NULL DEFAULT 0,
    tong_thuc_linh NUMERIC(18,0) NOT NULL DEFAULT 0,
    tong_chi_phi_dn NUMERIC(18,0) NOT NULL DEFAULT 0,
    nguoi_chot   BIGINT,
    cap_nhat     TIMESTAMP DEFAULT now()
);

-- ===== Phụ cấp phát sinh trong kỳ + khấu trừ nghỉ không phép / đi trễ / khác =====
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS phu_cap_khac    NUMERIC(18,0) NOT NULL DEFAULT 0; -- thưởng/phụ cấp phát sinh trong kỳ
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS ngay_nghi_kpep  NUMERIC(4,1)  NOT NULL DEFAULT 0; -- số ngày nghỉ không phép
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS so_phut_di_tre  INT           NOT NULL DEFAULT 0; -- tổng số phút đi trễ
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS khau_tru_nghi   NUMERIC(18,0) NOT NULL DEFAULT 0; -- tiền trừ nghỉ KP (tính)
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS khau_tru_tre    NUMERIC(18,0) NOT NULL DEFAULT 0; -- tiền trừ đi trễ (tính)
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS khau_tru_khac   NUMERIC(18,0) NOT NULL DEFAULT 0; -- khấu trừ khác (sau thuế)
