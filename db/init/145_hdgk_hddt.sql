-- 145: HOA DON BAN cua CONG TY den qua CONG HDDT (MISA meInvoice no-reply@meinvoice.vn gui ban sao ve hop thu).
--   Luong hoa don MUA nhan ra ben ban la chinh cong ty -> ghi vao kt_hd_gui_khach (nguon HDDT) thay vi hang cho mua;
--   khop hoa don ban theo so -> da gui khach + HDDT da phat hanh; chua co hoa don ban -> ke toan tao tu dong thu.
--   kt_hoa_don_cho.trang_thai them gia tri HD_BAN (dong da chuyen sang luong hoa don ban).
ALTER TABLE kt_hd_gui_khach ADD COLUMN IF NOT EXISTS nguon VARCHAR(12);            -- BCC | HDDT
ALTER TABLE kt_hd_gui_khach ADD COLUMN IF NOT EXISTS tien_truoc_thue NUMERIC(18,0);
ALTER TABLE kt_hd_gui_khach ADD COLUMN IF NOT EXISTS tien_thue NUMERIC(18,0);
ALTER TABLE kt_hd_gui_khach ADD COLUMN IF NOT EXISTS link_tra_cuu VARCHAR(300);
ALTER TABLE kt_hd_gui_khach ADD COLUMN IF NOT EXISTS ma_tra_cuu VARCHAR(40);
ALTER TABLE kt_hd_gui_khach ADD COLUMN IF NOT EXISTS noi_dung TEXT;
UPDATE kt_hd_gui_khach SET nguon = 'BCC' WHERE nguon IS NULL;
