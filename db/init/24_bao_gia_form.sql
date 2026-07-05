-- Báo giá soạn theo mẫu chuyên nghiệp (form đầy đủ, xuất PDF).
-- noi_dung JSONB giữ toàn bộ form: số, tiêu đề, khách/ATTN, dòng hàng tự do,
-- VAT, điều khoản... => lưu tạm (NHAP) chỉnh sửa nhiều lần rồi xuất PDF.
CREATE TABLE IF NOT EXISTS bao_gia_form (
    id            BIGSERIAL PRIMARY KEY,
    so            VARCHAR(50),
    khach_hang_id BIGINT REFERENCES khach_hang(id),
    noi_dung      JSONB NOT NULL,
    trang_thai    VARCHAR(20) NOT NULL DEFAULT 'NHAP',   -- NHAP / DA_XUAT
    nguoi_tao     BIGINT REFERENCES nhan_vien(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
