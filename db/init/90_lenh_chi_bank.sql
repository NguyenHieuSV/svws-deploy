-- 90: Duyệt chi Ngân Hàng — mỗi lệnh chi (tick ☑ Thanh toán) phải được DUYỆT trước khi
-- đổ về Kế toán để thực chi; lưu lịch sử thực chi theo từng ngày.
CREATE TABLE IF NOT EXISTS lenh_chi_bank (
  id BIGSERIAL PRIMARY KEY,
  don_mua_id BIGINT REFERENCES don_mua(id),
  so_tien NUMERIC(18,0) DEFAULT 0,
  de_nghi_luc TIMESTAMP,
  trang_thai VARCHAR(12) DEFAULT 'CHO_DUYET',   -- CHO_DUYET | DA_DUYET | TU_CHOI | DA_CHI
  duyet_luc TIMESTAMP,
  nguoi_duyet BIGINT REFERENCES nguoi_dung(id),
  chi_luc TIMESTAMP,
  ghi_chu VARCHAR(200)
);
-- Chuyển tiếp: các PO đang chờ lệnh ngân hàng từ trước được đưa vào hàng chờ duyệt (chạy 1 lần)
INSERT INTO lenh_chi_bank (don_mua_id, so_tien, de_nghi_luc, trang_thai)
SELECT dm.id, COALESCE(dm.lenh_bank_tien, 0), dm.lenh_bank_luc, 'CHO_DUYET'
FROM don_mua dm
WHERE dm.cho_lenh_bank IS TRUE
  AND NOT EXISTS (SELECT 1 FROM lenh_chi_bank l
                  WHERE l.don_mua_id = dm.id AND l.trang_thai IN ('CHO_DUYET', 'DA_DUYET'));
