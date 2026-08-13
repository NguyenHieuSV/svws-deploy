-- 89: Cấp hạn mức duyệt ĐƠN MUA (PO) cho Trưởng P. Quản lý nội bộ — ngang TP Cung ứng (đến 25 triệu)
INSERT INTO han_muc_duyet (loai, vai_tro_id, nguong_tu, nguong_den)
SELECT 'po', id, 0, 25000000 FROM vai_tro WHERE ma = 'TP_QLNB'
ON CONFLICT (loai, vai_tro_id) DO UPDATE
  SET nguong_tu = EXCLUDED.nguong_tu, nguong_den = EXCLUDED.nguong_den;
