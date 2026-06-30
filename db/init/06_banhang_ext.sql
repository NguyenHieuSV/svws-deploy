-- ============================================================
-- Mở rộng Bán hàng: lưu tệp PO/Hợp đồng + email chào hàng có duyệt
-- (chạy SAU SVWS_schema.sql)
-- ============================================================
ALTER TABLE khach_hang ADD COLUMN IF NOT EXISTS email VARCHAR(120);

-- Tệp đính kèm (PO, hợp đồng...) — gắn vào đơn hàng / báo giá / khách hàng
CREATE TABLE IF NOT EXISTS tep_dinh_kem (
    id           BIGSERIAL PRIMARY KEY,
    doi_tuong    VARCHAR(20)  NOT NULL,           -- DON_HANG / BAO_GIA / KHACH_HANG
    doi_tuong_id BIGINT       NOT NULL,
    loai         VARCHAR(20)  NOT NULL DEFAULT 'KHAC',  -- PO / HOP_DONG / KHAC
    ten_file     VARCHAR(255) NOT NULL,
    duong_dan    VARCHAR(500) NOT NULL,
    kich_thuoc   BIGINT,
    content_type VARCHAR(100),
    nguoi_tai_len BIGINT REFERENCES nhan_vien(id),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tep_dt ON tep_dinh_kem(doi_tuong, doi_tuong_id);

-- Chiến dịch email chào hàng (nội dung phải được duyệt trước khi gửi)
CREATE TABLE IF NOT EXISTS chien_dich_email (
    id          BIGSERIAL PRIMARY KEY,
    ten         VARCHAR(200) NOT NULL,
    tieu_de     VARCHAR(300) NOT NULL,
    noi_dung    TEXT NOT NULL,                    -- hỗ trợ {ten_kh}
    bo_loc_abc  VARCHAR(3),                       -- A/B/C hoặc NULL = tất cả
    trang_thai  VARCHAR(20) NOT NULL DEFAULT 'CHO_DUYET', -- CHO_DUYET/DA_DUYET/DA_GUI/TU_CHOI
    nguoi_tao   BIGINT REFERENCES nhan_vien(id),
    nguoi_duyet BIGINT REFERENCES nhan_vien(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS email_log (
    id            BIGSERIAL PRIMARY KEY,
    chien_dich_id BIGINT REFERENCES chien_dich_email(id) ON DELETE CASCADE,
    khach_hang_id BIGINT REFERENCES khach_hang(id),
    email         VARCHAR(120),
    trang_thai    VARCHAR(20),                    -- GUI_OK / LOI / BO_QUA
    ghi_chu       VARCHAR(255),
    thoi_diem     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_email_log_cd ON email_log(chien_dich_id);

-- Nhật ký liên lạc KH — hệ thống là nơi ghi nhận DUY NHẤT mọi trao đổi với khách
CREATE TABLE IF NOT EXISTS lien_lac (
    id            BIGSERIAL PRIMARY KEY,
    khach_hang_id BIGINT NOT NULL REFERENCES khach_hang(id) ON DELETE CASCADE,
    kenh          VARCHAR(15) NOT NULL DEFAULT 'EMAIL',  -- EMAIL / GOI / GAP / GHI_CHU
    huong         VARCHAR(5)  NOT NULL DEFAULT 'DI',      -- DI (gửi đi) / DEN (nhận về)
    tieu_de       VARCHAR(300),
    noi_dung      TEXT,
    lien_quan_loai VARCHAR(15),                           -- BAO_GIA / DON_HANG / HOP_DONG
    lien_quan_id  BIGINT,
    gui_tu        VARCHAR(120),                           -- địa chỉ gửi (công ty)
    nguoi_xu_ly   BIGINT REFERENCES nhan_vien(id),
    trang_thai    VARCHAR(15),                            -- GUI_OK / LOI / GHI_NHAN
    thoi_diem     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_lien_lac_kh ON lien_lac(khach_hang_id);

-- Chiến dịch có thể nhắm tới danh sách khách cụ thể (ngoài lọc ABC)
ALTER TABLE chien_dich_email ADD COLUMN IF NOT EXISTS khach_hang_ids TEXT;

-- Giai đoạn 1: thu thư phản hồi (inbound) vào hệ thống
ALTER TABLE lien_lac ALTER COLUMN khach_hang_id DROP NOT NULL;     -- cho phép thư chưa gắn KH
ALTER TABLE lien_lac ADD COLUMN IF NOT EXISTS tu_email   VARCHAR(120);
ALTER TABLE lien_lac ADD COLUMN IF NOT EXISTS message_id VARCHAR(255);
ALTER TABLE lien_lac ADD COLUMN IF NOT EXISTS da_xu_ly   BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_lien_lac_msgid ON lien_lac(message_id);

-- Giai đoạn 2: phân loại AI + tự xử lý + giao việc kèm SLA
ALTER TABLE khach_hang ADD COLUMN IF NOT EXISTS khong_nhan_email BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE lien_lac ADD COLUMN IF NOT EXISTS ai_y_dinh  VARCHAR(20);
ALTER TABLE lien_lac ADD COLUMN IF NOT EXISTS ai_khan    VARCHAR(10);   -- CAO/TRUNG/THAP
ALTER TABLE lien_lac ADD COLUMN IF NOT EXISTS ai_tom_tat TEXT;
ALTER TABLE lien_lac ADD COLUMN IF NOT EXISTS ai_tra_loi TEXT;          -- nội dung trả lời gợi ý

CREATE TABLE IF NOT EXISTS cong_viec (
    id            BIGSERIAL PRIMARY KEY,
    lien_lac_id   BIGINT REFERENCES lien_lac(id) ON DELETE SET NULL,
    khach_hang_id BIGINT REFERENCES khach_hang(id) ON DELETE CASCADE,
    loai          VARCHAR(20),
    tieu_de       VARCHAR(300) NOT NULL,
    mo_ta         TEXT,
    nguoi_phu_trach BIGINT REFERENCES nhan_vien(id),
    uu_tien       VARCHAR(10) DEFAULT 'TRUNG',
    han_xu_ly     TIMESTAMPTZ,
    trang_thai    VARCHAR(15) NOT NULL DEFAULT 'MO',   -- MO/DANG_XU_LY/XONG
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cv_pt ON cong_viec(nguoi_phu_trach);
CREATE INDEX IF NOT EXISTS idx_cv_tt ON cong_viec(trang_thai);

-- Giai đoạn 3: cơ hội (pipeline CRM) + auto báo giá + dashboard + SLA hoàn thành
ALTER TABLE cong_viec ADD COLUMN IF NOT EXISTS hoan_thanh_luc TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS co_hoi (
    id            BIGSERIAL PRIMARY KEY,
    khach_hang_id BIGINT REFERENCES khach_hang(id) ON DELETE CASCADE,
    lien_lac_id   BIGINT REFERENCES lien_lac(id)  ON DELETE SET NULL,
    bao_gia_id    BIGINT REFERENCES bao_gia(id)   ON DELETE SET NULL,
    don_hang_id   BIGINT REFERENCES don_hang(id)  ON DELETE SET NULL,
    nguon         VARCHAR(20) DEFAULT 'EMAIL',
    tieu_de       VARCHAR(300),
    giai_doan     VARCHAR(15) NOT NULL DEFAULT 'MOI',  -- MOI/QUAN_TAM/BAO_GIA/DAM_PHAN/THANG/THUA
    gia_tri_dk    NUMERIC(18,0) DEFAULT 0,
    nguoi_phu_trach BIGINT REFERENCES nhan_vien(id),
    ly_do_thua    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_cohoi_kh ON co_hoi(khach_hang_id);
CREATE INDEX IF NOT EXISTS idx_cohoi_gd ON co_hoi(giai_doan);
