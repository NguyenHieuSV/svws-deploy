-- ============ THAM SỐ LƯƠNG THEO LUẬT (cập nhật khi luật thay đổi) ============
CREATE TABLE IF NOT EXISTS tham_so_luong (
    id INT PRIMARY KEY DEFAULT 1,
    tl_bhxh_nv NUMERIC(6,4) NOT NULL DEFAULT 0.08,
    tl_bhyt_nv NUMERIC(6,4) NOT NULL DEFAULT 0.015,
    tl_bhtn_nv NUMERIC(6,4) NOT NULL DEFAULT 0.01,
    tl_bhxh_dn NUMERIC(6,4) NOT NULL DEFAULT 0.175,
    tl_bhyt_dn NUMERIC(6,4) NOT NULL DEFAULT 0.03,
    tl_bhtn_dn NUMERIC(6,4) NOT NULL DEFAULT 0.01,
    tran_bhxh_bhyt NUMERIC(18,0) NOT NULL DEFAULT 46800000,   -- 20× lương cơ sở
    tran_bhtn      NUMERIC(18,0) NOT NULL DEFAULT 99200000,   -- 20× LTT vùng I
    giam_tru_ban_than  NUMERIC(18,0) NOT NULL DEFAULT 11000000,
    giam_tru_phu_thuoc NUMERIC(18,0) NOT NULL DEFAULT 4400000,
    mien_thue_an   NUMERIC(18,0) NOT NULL DEFAULT 730000,
    hs_ot_thuong   NUMERIC(4,2) NOT NULL DEFAULT 1.5,
    hs_ot_cuoi_tuan NUMERIC(4,2) NOT NULL DEFAULT 2.0,
    hs_ot_le       NUMERIC(4,2) NOT NULL DEFAULT 3.0,
    luong_co_so    NUMERIC(18,0) NOT NULL DEFAULT 2340000,
    luong_toi_thieu_vung NUMERIC(18,0) NOT NULL DEFAULT 4960000,
    bac_thue TEXT NOT NULL DEFAULT '[[5000000,0.05],[10000000,0.10],[18000000,0.15],[32000000,0.20],[52000000,0.25],[80000000,0.30],[null,0.35]]',
    cap_nhat TIMESTAMP DEFAULT now(),
    CONSTRAINT ts_luong_mot_dong CHECK (id = 1)
);
INSERT INTO tham_so_luong (id) VALUES (1) ON CONFLICT (id) DO NOTHING;
