-- ============ KẾ TOÁN: Quỹ tiền + Phiếu thu/chi (duyệt nhiều cấp) + truy vết mã hàng bán ============

-- Quỹ tiền mặt / tài khoản ngân hàng (quản lý tiền)
CREATE TABLE IF NOT EXISTS tai_khoan_quy (
    id          BIGSERIAL PRIMARY KEY,
    ma          VARCHAR(20) UNIQUE NOT NULL,
    ten         VARCHAR(120) NOT NULL,
    loai        VARCHAR(12) NOT NULL DEFAULT 'TIEN_MAT',   -- TIEN_MAT | NGAN_HANG
    so_tk       VARCHAR(40),                               -- số tài khoản NH
    tk_ke_toan  VARCHAR(20) NOT NULL DEFAULT '111',        -- 111/112
    so_du_dau   NUMERIC(18,0) NOT NULL DEFAULT 0,
    so_du       NUMERIC(18,0) NOT NULL DEFAULT 0,
    hoat_dong   BOOLEAN NOT NULL DEFAULT TRUE
);

-- Phiếu thu / phiếu chi — chứng từ tiền mặt với luồng duyệt nhiều cấp
CREATE TABLE IF NOT EXISTS phieu_thu_chi (
    id            BIGSERIAL PRIMARY KEY,
    so            VARCHAR(30) UNIQUE,
    loai          VARCHAR(4) NOT NULL,                     -- THU | CHI
    ngay          DATE NOT NULL DEFAULT CURRENT_DATE,
    quy_id        BIGINT NOT NULL REFERENCES tai_khoan_quy(id),
    doi_tac_loai  VARCHAR(8),                              -- KH | NCC | KHAC
    khach_hang_id BIGINT REFERENCES khach_hang(id),
    nha_cung_cap_id BIGINT REFERENCES nha_cung_cap(id),
    so_tien       NUMERIC(18,0) NOT NULL,
    dien_giai     VARCHAR(200),
    don_hang_id   BIGINT REFERENCES don_hang(id),          -- MÃ HÀNG BÁN (truy vết)
    cong_no_id    BIGINT REFERENCES cong_no(id),           -- cấn trừ công nợ
    tk_doi_ung    VARCHAR(20),                             -- tài khoản đối ứng
    trang_thai    VARCHAR(12) NOT NULL DEFAULT 'NHAP',     -- NHAP|CHO_DUYET|DA_DUYET|TU_CHOI|HUY
    nguoi_tao     BIGINT REFERENCES nhan_vien(id),
    nguoi_duyet   BIGINT REFERENCES nhan_vien(id),
    ngay_duyet    DATE,
    but_toan_id   BIGINT REFERENCES but_toan(id),
    ghi_chu       TEXT
);
CREATE INDEX IF NOT EXISTS idx_ptc_trangthai ON phieu_thu_chi(trang_thai);
CREATE INDEX IF NOT EXISTS idx_ptc_donhang ON phieu_thu_chi(don_hang_id);

-- Bút toán sổ cái: bổ sung truy vết theo mã hàng bán + quỹ + nguồn chứng từ
ALTER TABLE but_toan ADD COLUMN IF NOT EXISTS don_hang_id BIGINT REFERENCES don_hang(id);
ALTER TABLE but_toan ADD COLUMN IF NOT EXISTS quy_id      BIGINT REFERENCES tai_khoan_quy(id);
ALTER TABLE but_toan ADD COLUMN IF NOT EXISTS nguon       VARCHAR(20);
ALTER TABLE but_toan ADD COLUMN IF NOT EXISTS nguon_id    BIGINT;

-- Quỹ mặc định
INSERT INTO tai_khoan_quy (ma, ten, loai, tk_ke_toan)
VALUES ('QTM','Quỹ tiền mặt','TIEN_MAT','111'),
       ('NH-VCB','Tài khoản Vietcombank','NGAN_HANG','112')
ON CONFLICT (ma) DO NOTHING;

-- Hạn mức duyệt phiếu thu/chi (nhiều cấp): KTT ≤ 50tr, CEO không giới hạn
INSERT INTO han_muc_duyet (loai, vai_tro_id, nguong_tu, nguong_den)
SELECT v.loai, vt.id, v.tu, v.den
FROM (VALUES
  ('thu_chi','KTT',0,50000000),
  ('thu_chi','CEO',50000001,NULL::numeric)
) AS v(loai, ma, tu, den)
JOIN vai_tro vt ON vt.ma = v.ma
ON CONFLICT (loai, vai_tro_id) DO UPDATE SET nguong_tu = EXCLUDED.nguong_tu, nguong_den = EXCLUDED.nguong_den;

-- ============ Hóa đơn mua/bán: bổ sung trường để quản lý & kiểm soát ============
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS so              VARCHAR(40);
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS khach_hang_id   BIGINT REFERENCES khach_hang(id);
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS nha_cung_cap_id BIGINT REFERENCES nha_cung_cap(id);
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS tk_chi_phi      VARCHAR(20);   -- TK chi phí/giá vốn cho HĐ mua (632/642/641/627)
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS dien_giai       VARCHAR(200);
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS da_hach_toan    BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE hoa_don ADD COLUMN IF NOT EXISTS trang_thai      VARCHAR(20) NOT NULL DEFAULT 'GHI_NHAN';
CREATE INDEX IF NOT EXISTS idx_hoadon_loai ON hoa_don(loai);

-- ============ Tạm ứng / Trả trước theo mã hàng bán (trước khi có hóa đơn) ============
ALTER TABLE phieu_thu_chi ADD COLUMN IF NOT EXISTS la_tam_ung BOOLEAN NOT NULL DEFAULT FALSE;  -- phiếu thu/chi là khoản tạm ứng/trả trước
ALTER TABLE phieu_thu_chi ADD COLUMN IF NOT EXISTS da_can_tru NUMERIC(18,0) NOT NULL DEFAULT 0; -- phần tạm ứng đã cấn trừ vào hóa đơn
CREATE INDEX IF NOT EXISTS idx_ptc_tamung ON phieu_thu_chi(don_hang_id, la_tam_ung);

-- ============ Cam kết đặt cọc trên đơn hàng (mã hàng bán) ============
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS ty_le_dat_coc NUMERIC(5,2) NOT NULL DEFAULT 0;  -- % đặt cọc dự kiến
