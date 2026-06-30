-- ============================================================
-- Mở rộng cho module CRM (chạy SAU SVWS_schema.sql)
--   - lịch/lịch sử chăm sóc khách hàng (gồm khiếu nại, CSAT)
-- (Hồ sơ KH + phân loại ABC đã có sẵn trong bảng khach_hang)
-- ============================================================
CREATE TABLE IF NOT EXISTS cham_soc_kh (
    id           BIGSERIAL PRIMARY KEY,
    khach_hang_id BIGINT NOT NULL REFERENCES khach_hang(id) ON DELETE CASCADE,
    loai         VARCHAR(20) NOT NULL,            -- GOI / EMAIL / KHIEU_NAI / SINH_NHAT
    noi_dung     VARCHAR(300),
    ngay_hen     DATE,
    ngay_thuc_hien DATE,
    trang_thai   VARCHAR(20) NOT NULL DEFAULT 'CHO',   -- CHO / HOAN_THANH
    csat         NUMERIC(2,1),                    -- điểm hài lòng 1..5
    nguoi_phu_trach BIGINT REFERENCES nhan_vien(id),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cham_soc_kh_kh  ON cham_soc_kh(khach_hang_id);
CREATE INDEX IF NOT EXISTS idx_cham_soc_kh_hen ON cham_soc_kh(ngay_hen);
