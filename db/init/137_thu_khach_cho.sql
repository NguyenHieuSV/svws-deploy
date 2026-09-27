-- 137: THU KHACH HANG ve HOA DON BAN / THANH TOAN (Ke toan) — AI doc thu khach: xac nhan nhan HD, bao chuyen khoan,
-- yeu cau dieu chinh, hoi hoa don → hang CHO XAC NHAN, khop khach / hoa don ban / cong no phai thu. Vao lich quet tuan.
CREATE TABLE IF NOT EXISTS kt_thu_khach_cho (
  id BIGSERIAL PRIMARY KEY,
  message_id VARCHAR(250) UNIQUE,
  tu_email VARCHAR(160),
  tieu_de VARCHAR(250),
  noi_dung TEXT,
  ngay_thu DATE,
  khach_hang_id BIGINT REFERENCES khach_hang(id) ON DELETE SET NULL,
  ai_khach_ten VARCHAR(200),
  loai VARCHAR(24) NOT NULL DEFAULT 'KHAC',      -- XAC_NHAN_NHAN_HD | THONG_BAO_THANH_TOAN | YEU_CAU_DIEU_CHINH | HOI_HOA_DON | KHAC
  so_hoa_don VARCHAR(80),
  so_tien NUMERIC(18,0),
  ngay_chuyen DATE,
  ngan_hang VARCHAR(120),
  ma_don VARCHAR(60),
  ai_tom_tat VARCHAR(400),
  hoa_don_id BIGINT,
  cong_no_id BIGINT,
  trang_thai VARCHAR(16) NOT NULL DEFAULT 'CHO_XAC_NHAN',   -- CHO_XAC_NHAN | DA_XU_LY | BO_QUA
  ket_qua JSONB,
  nguoi_xu_ly BIGINT,
  xu_ly_luc TIMESTAMP,
  tao_luc TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tkc_tt ON kt_thu_khach_cho(trang_thai);
