-- 154 — Báo cáo ngày (Working time & Report): thông tin giao việc + nhật ký NHẮC chưa báo cáo (26/10/2026).
--  • bao_cao_ngay: người được giao việc (email), tên công việc, ngày bắt đầu / kết thúc.
--  • bao_cao_nhac: mỗi (ngày, nhân viên) chỉ nhắc MỘT lần — khởi động lại máy chủ không nhắn trùng.
ALTER TABLE bao_cao_ngay ADD COLUMN IF NOT EXISTS giao_viec_email VARCHAR(150);
ALTER TABLE bao_cao_ngay ADD COLUMN IF NOT EXISTS ten_cong_viec   VARCHAR(250);
ALTER TABLE bao_cao_ngay ADD COLUMN IF NOT EXISTS cv_bat_dau      DATE;
ALTER TABLE bao_cao_ngay ADD COLUMN IF NOT EXISTS cv_ket_thuc     DATE;

CREATE TABLE IF NOT EXISTS bao_cao_nhac (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ngay DATE NOT NULL,                                                  -- ngày báo cáo bị thiếu
  nhan_vien_id BIGINT NOT NULL REFERENCES nhan_vien(id) ON DELETE CASCADE,
  nguon VARCHAR(10) NOT NULL DEFAULT 'TU_DONG',                        -- TU_DONG | TAY
  ket_qua VARCHAR(10) NOT NULL DEFAULT 'OK',                           -- OK | LOI
  loi TEXT,
  nguoi_gui BIGINT REFERENCES nguoi_dung(id) ON DELETE SET NULL,
  tao_luc TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_bao_cao_nhac_ngay_nv ON bao_cao_nhac (ngay, nhan_vien_id);
