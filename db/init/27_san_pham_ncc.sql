-- ============================================================
-- SVWS 27 — Danh mục SẢN PHẨM của nhà cung cấp
--   Dữ liệu nguồn cho bộ phận mua hàng và dự toán báo giá:
--   tên SP, mã SP, mô tả, nhà sản xuất, đơn vị, đơn giá.
-- ============================================================
CREATE TABLE IF NOT EXISTS san_pham_ncc (
    id              BIGSERIAL PRIMARY KEY,
    nha_cung_cap_id BIGINT NOT NULL REFERENCES nha_cung_cap(id) ON DELETE CASCADE,
    ten             VARCHAR(250) NOT NULL,
    ma_sp           VARCHAR(60),
    mo_ta           TEXT,
    nha_san_xuat    VARCHAR(150),
    don_vi          VARCHAR(30),
    don_gia         NUMERIC(18,0) NOT NULL DEFAULT 0,
    ghi_chu         VARCHAR(300),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_spn_ncc ON san_pham_ncc(nha_cung_cap_id);
CREATE INDEX IF NOT EXISTS idx_spn_ten ON san_pham_ncc(ten);
