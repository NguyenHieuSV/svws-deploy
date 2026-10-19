-- 149 — TRAINING (mục Nội bộ, 19/10/2026): kho bài huấn luyện / bài thi (HTML tương tác, PDF, Office, video…) và ĐIỂM THI của từng nhân viên.
--   trn_bai      : mỗi dòng một bài (file lưu ở kho lưu trữ chung app/luu_tru.py, cột duong_dan là tham chiếu), có phiên bản (Rev).
--   trn_ket_qua  : mỗi lượt thi của một người dùng / nhân viên (điểm quy về %, đúng/tổng câu, đạt hay chưa, chi tiết từng nhóm câu).
-- Quyền: module riêng 'training' — mọi vai trò XEM (học, thi, xem điểm của mình); CEO / ADMIN QUẢN TRỊ (xóa bài, xóa kết quả);
-- NV Hành chính - Nhân sự + Trưởng P. Quản lý nội bộ THAO_TAC (tải bài lên, xem bảng điểm mọi người). CEO chỉnh tiếp ở ma trận Phân quyền.
CREATE TABLE IF NOT EXISTS trn_bai (
    id            BIGSERIAL PRIMARY KEY,
    tieu_de       VARCHAR(250) NOT NULL,
    loai          VARCHAR(16)  NOT NULL DEFAULT 'HUAN_LUYEN',   -- HUAN_LUYEN | THI | HUAN_LUYEN_THI
    mo_ta         TEXT,
    ten_file      VARCHAR(250),
    loai_tep      VARCHAR(10),                                  -- html | pdf | hinh | video | khac
    noi_dung_loai VARCHAR(120),
    duong_dan     TEXT,
    kich_thuoc    BIGINT NOT NULL DEFAULT 0,
    phien_ban     INTEGER NOT NULL DEFAULT 1,                   -- +1 mỗi lần thay file
    hien          BOOLEAN NOT NULL DEFAULT TRUE,                -- FALSE = chỉ người quản lý thấy
    diem_dat      NUMERIC(5,1),                                 -- ngưỡng đạt (%) nếu bài không tự báo
    nguoi_tao     BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
    tao_luc       TIMESTAMP NOT NULL DEFAULT now(),
    cap_nhat_luc  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trn_ket_qua (
    id             BIGSERIAL PRIMARY KEY,
    bai_id         BIGINT NOT NULL REFERENCES trn_bai(id) ON DELETE CASCADE,
    nguoi_dung_id  BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
    nhan_vien_id   BIGINT REFERENCES nhan_vien(id) ON DELETE SET NULL,
    ten_nguoi_thi  VARCHAR(150),                                -- lưu cứng tên tại lúc thi (đổi tên / nghỉ việc vẫn còn vết)
    ten_khai       VARCHAR(150),                                -- tên người thi tự nhập trong bài
    ma_nv_khai     VARCHAR(40),
    don_vi_khai    VARCHAR(120),
    chuc_danh_khai VARCHAR(120),
    diem           NUMERIC(6,1) NOT NULL,                       -- điểm quy về % (0–100)
    so_cau         INTEGER,
    so_dung        INTEGER,
    diem_dat       NUMERIC(6,1),                                -- ngưỡng đạt lúc thi (%)
    dat            BOOLEAN,
    lan_thi        INTEGER NOT NULL DEFAULT 1,                  -- lần thứ mấy của người này ở bài này
    phien_ban      INTEGER,                                     -- phiên bản bài lúc thi
    thoi_gian_giay INTEGER,
    chi_tiet       JSONB,
    nop_luc        TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_trn_kq_bai  ON trn_ket_qua(bai_id);
CREATE INDEX IF NOT EXISTS idx_trn_kq_nd   ON trn_ket_qua(nguoi_dung_id);
CREATE INDEX IF NOT EXISTS idx_trn_kq_nv   ON trn_ket_qua(nhan_vien_id);

-- Phân quyền module 'training': mọi vai trò XEM; CEO / ADMIN QUAN_TRI; NV_HCNS / TP_QLNB THAO_TAC (nếu vai trò tồn tại)
INSERT INTO phan_quyen (vai_tro_id, module, muc)
SELECT vt.id, 'training',
       CASE WHEN vt.ma IN ('CEO', 'ADMIN') THEN 'QUAN_TRI'::muc_quyen
            WHEN vt.ma IN ('NV_HCNS', 'TP_QLNB') THEN 'THAO_TAC'::muc_quyen
            ELSE 'XEM'::muc_quyen END
FROM vai_tro vt
ON CONFLICT (vai_tro_id, module) DO NOTHING;
