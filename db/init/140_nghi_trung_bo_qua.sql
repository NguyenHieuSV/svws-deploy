-- 140: NGHI TRUNG BO QUA — CEO xac nhan mot nhom nghi trung la hop le (khong canh bao / khong chan nua)
CREATE TABLE IF NOT EXISTS nghi_trung_bo_qua (
  id BIGSERIAL PRIMARY KEY,
  loai VARCHAR(12) NOT NULL,          -- HOA_DON | PO_TIEN | LENH_TIEN
  khoa VARCHAR(120) NOT NULL,         -- HOA_DON: ncc_id|so_hd_chuan ; PO_TIEN / LENH_TIEN: ncc_id|so_tien
  mo_ta VARCHAR(300),
  ly_do VARCHAR(300),
  nguoi_dung_id BIGINT,
  tao_luc TIMESTAMP DEFAULT NOW(),
  UNIQUE (loai, khoa)
);
