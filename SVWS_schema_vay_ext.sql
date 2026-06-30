-- ============ QUẢN LÝ TIỀN VAY (khế ước vay + lịch trả nợ) ============
CREATE TABLE IF NOT EXISTS khoan_vay (
    id            BIGSERIAL PRIMARY KEY,
    so            VARCHAR(40) UNIQUE,
    ben_cho_vay   VARCHAR(160) NOT NULL,
    loai          VARCHAR(12)  NOT NULL DEFAULT 'NGAN_HAN',  -- NGAN_HAN / DAI_HAN
    so_tien_goc   NUMERIC(18,0) NOT NULL,
    lai_suat_nam  NUMERIC(6,3)  NOT NULL DEFAULT 0,           -- %/năm
    phuong_thuc   VARCHAR(16)  NOT NULL DEFAULT 'GOC_DEU',    -- GOC_DEU / TRA_DEU / GOC_CUOI
    ngay_nhan     DATE NOT NULL,
    so_ky         INT  NOT NULL DEFAULT 12,
    chu_ky_thang  INT  NOT NULL DEFAULT 1,                    -- số tháng mỗi kỳ
    ngay_dao_han  DATE,
    tk_tien       VARCHAR(10) NOT NULL DEFAULT '112',         -- 111/112 nhận & trả
    con_lai_goc   NUMERIC(18,0) NOT NULL DEFAULT 0,
    trang_thai    VARCHAR(16) NOT NULL DEFAULT 'DANG_VAY',    -- DANG_VAY / DA_TAT_TOAN
    ghi_chu       TEXT,
    cap_nhat      TIMESTAMP DEFAULT now()
);
CREATE TABLE IF NOT EXISTS lich_tra_no (
    id            BIGSERIAL PRIMARY KEY,
    khoan_vay_id  BIGINT NOT NULL REFERENCES khoan_vay(id) ON DELETE CASCADE,
    ky            INT NOT NULL,
    ngay_den_han  DATE NOT NULL,
    du_no_dau     NUMERIC(18,0) NOT NULL DEFAULT 0,
    goc_phai_tra  NUMERIC(18,0) NOT NULL DEFAULT 0,
    lai_phai_tra  NUMERIC(18,0) NOT NULL DEFAULT 0,
    tong_phai_tra NUMERIC(18,0) NOT NULL DEFAULT 0,
    du_no_cuoi    NUMERIC(18,0) NOT NULL DEFAULT 0,
    da_tra        BOOLEAN NOT NULL DEFAULT FALSE,
    ngay_tra      DATE,
    UNIQUE(khoan_vay_id, ky)
);
CREATE INDEX IF NOT EXISTS idx_lichtrano_denhan ON lich_tra_no(ngay_den_han, da_tra);
