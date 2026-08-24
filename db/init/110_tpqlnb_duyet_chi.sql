-- 110: TP Quản lý nội bộ được DUYỆT CHI đến 30 triệu (lệnh chi ngân hàng + phiếu thu-chi).
-- Trần tiền do bảng han_muc_duyet quyết định; vẫn áp dụng TÁCH VAI (không tự duyệt lệnh mình đề nghị).
INSERT INTO han_muc_duyet (loai, vai_tro_id, nguong_tu, nguong_den)
SELECT 'thu_chi', id, 0, 30000000 FROM vai_tro WHERE ma = 'TP_QLNB'
ON CONFLICT (loai, vai_tro_id) DO UPDATE
  SET nguong_tu = EXCLUDED.nguong_tu, nguong_den = EXCLUDED.nguong_den;

-- Nâng quyền module kế toán XEM -> DUYET để duyệt được phiếu thu-chi (số tiền vẫn bị trần 30tr ở trên)
UPDATE phan_quyen SET muc = 'DUYET'
WHERE module = 'ke_toan' AND muc = 'XEM'
  AND vai_tro_id = (SELECT id FROM vai_tro WHERE ma = 'TP_QLNB');
