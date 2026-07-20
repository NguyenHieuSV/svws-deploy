-- 48_po_vat.sql — VAT cho đơn mua (PO). Trước đây PO chỉ có tổng chưa thuế,
-- nên công nợ phải trả thiếu VAT, không khớp hóa đơn thực tế của NCC.
-- Nay: VAT theo TỪNG DÒNG hàng (mỗi mặt hàng một mức %), tong_tien = tiền hàng + tiền thuế.
ALTER TABLE don_mua_ct ADD COLUMN IF NOT EXISTS thue_suat NUMERIC(5,2) NOT NULL DEFAULT 0;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS tien_hang NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS tien_thue NUMERIC(18,0) NOT NULL DEFAULT 0;
-- PO cũ chưa có VAT: tiền hàng = tổng hiện có, tiền thuế = 0, tong_tien giữ nguyên.
UPDATE don_mua SET tien_hang = tong_tien WHERE tien_hang = 0;
