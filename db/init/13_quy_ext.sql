-- ============ TRÍCH LẬP QUỸ (phân biệt được trừ / sau thuế) + cảnh báo trần ============
CREATE TABLE IF NOT EXISTS quy_trich_lap (
    ma        VARCHAR(20) PRIMARY KEY,
    ten       VARCHAR(160) NOT NULL,
    ban_chat  VARCHAR(12) NOT NULL DEFAULT 'TRUOC_THUE',  -- TRUOC_THUE (được trừ) / SAU_THUE (không được trừ)
    tk_no     VARCHAR(10) NOT NULL,
    tk_co     VARCHAR(10) NOT NULL,
    gioi_han  VARCHAR(20) NOT NULL DEFAULT 'NONE',          -- NONE / KHCN_20 / PHUC_LOI_1THANG
    so_du     NUMERIC(18,0) NOT NULL DEFAULT 0,
    hoat_dong BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS giao_dich_quy (
    id         BIGSERIAL PRIMARY KEY,
    ma_quy     VARCHAR(20) NOT NULL REFERENCES quy_trich_lap(ma),
    loai       VARCHAR(12) NOT NULL,                         -- TRICH_LAP / SU_DUNG
    ky         VARCHAR(7)  NOT NULL,                         -- 'YYYY' hoặc 'YYYY-MM'
    ngay       DATE NOT NULL DEFAULT CURRENT_DATE,
    so_tien    NUMERIC(18,0) NOT NULL,
    dien_giai  TEXT,
    but_toan_id BIGINT,
    nguoi_tao  BIGINT,
    ngay_tao   TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_gdquy_ky ON giao_dich_quy(ma_quy, ky);

INSERT INTO quy_trich_lap (ma, ten, ban_chat, tk_no, tk_co, gioi_han) VALUES
 ('DP_PTKD','Dự phòng nợ phải thu khó đòi','TRUOC_THUE','642','2293','NONE'),
 ('DP_HTK','Dự phòng giảm giá hàng tồn kho','TRUOC_THUE','632','2294','NONE'),
 ('DP_DAUTU','Dự phòng giảm giá đầu tư tài chính','TRUOC_THUE','635','2291','NONE'),
 ('DP_BAOHANH','Dự phòng bảo hành sản phẩm/công trình','TRUOC_THUE','641','352','NONE'),
 ('KHCN','Quỹ phát triển khoa học & công nghệ','TRUOC_THUE','642','356','KHCN_20'),
 ('KHEN_THUONG','Quỹ khen thưởng','SAU_THUE','421','3531','NONE'),
 ('PHUC_LOI','Quỹ phúc lợi','SAU_THUE','421','3532','PHUC_LOI_1THANG'),
 ('DAUTU_PT','Quỹ đầu tư phát triển','SAU_THUE','421','414','NONE'),
 ('DP_TAICHINH','Quỹ dự phòng tài chính','SAU_THUE','421','418','NONE')
ON CONFLICT (ma) DO NOTHING;
