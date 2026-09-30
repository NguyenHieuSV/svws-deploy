-- 141: HOA DON CHO (AI doc tu email) <-> PO cua NCC
--   don_mua_id : PO goi y (may do theo so HD / so tien) hoac ke toan chon
--   po_khop    : cach khop  SO_HD | TIEN | TIEN_TRUOC (+n ung vien khac) | TAY (ke toan chon) | BO (ke toan bo lien ket)
-- Khi ke toan xac nhan Ghi: so HD + ngay HD dien len PO va cong no phai tra; PO da co hoa don nhap HDM- cung tien
-- thi hoa don nhap nhan so that (khong tao hoa don thu hai).
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS don_mua_id BIGINT;
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS po_khop VARCHAR(20);
