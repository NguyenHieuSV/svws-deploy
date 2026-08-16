-- 97: Hóa đơn MUA từ email — cột tài khoản chi phí tự phân loại (632/642/641/627)
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS tk_chi_phi VARCHAR(10);
