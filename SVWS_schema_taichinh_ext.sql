-- ============ Tham số tài chính khai báo (cho bảng cân đối + dự báo dòng tiền) ============
CREATE TABLE IF NOT EXISTS tham_so_tai_chinh (
    id                BIGINT PRIMARY KEY DEFAULT 1,
    von_chu_so_huu    NUMERIC(18,0) NOT NULL DEFAULT 0,   -- vốn chủ sở hữu
    tai_san_co_dinh   NUMERIC(18,0) NOT NULL DEFAULT 0,   -- TSCĐ thuần (đã trừ khấu hao)
    no_dai_han        NUMERIC(18,0) NOT NULL DEFAULT 0,   -- vay/nợ dài hạn
    chi_co_dinh_thang NUMERIC(18,0) NOT NULL DEFAULT 0,   -- chi phí cố định/tháng (lương, thuê...) cho dự báo
    cap_nhat          TIMESTAMP DEFAULT now(),
    CONSTRAINT chi_mot_dong CHECK (id = 1)
);
INSERT INTO tham_so_tai_chinh (id) VALUES (1) ON CONFLICT (id) DO NOTHING;
