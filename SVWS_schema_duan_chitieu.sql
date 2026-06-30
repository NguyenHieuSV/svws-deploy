-- ===== Chất lượng đầu vào / chỉ tiêu giới hạn đầu ra =====
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS tieu_chuan_dau_ra VARCHAR(160);

CREATE TABLE IF NOT EXISTS du_an_chi_tieu (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    thu_tu      INT DEFAULT 0,
    ten         VARCHAR(120) NOT NULL,        -- vd COD, BOD5, TSS, Độ màu, NH4-N, Bụi, SO2...
    don_vi      VARCHAR(40),                  -- mg/L, Pt-Co, mg/Nm³...
    gia_tri_vao NUMERIC(18,4),                -- chất lượng đầu vào (đo/thiết kế)
    gioi_han_ra NUMERIC(18,4),                -- giới hạn kiểm soát đầu ra (theo tiêu chuẩn hoặc tự nhập)
    ghi_chu     VARCHAR(200)                  -- vd "cột B", "pH 6-9", nguồn giá trị
);
CREATE INDEX IF NOT EXISTS idx_dactieu ON du_an_chi_tieu(du_an_id, thu_tu);
