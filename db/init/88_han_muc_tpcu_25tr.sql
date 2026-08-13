-- 88: Nâng trần duyệt ĐƠN MUA (PO) của TP Cung ứng & Kho: 10 triệu → 25 triệu
UPDATE han_muc_duyet SET nguong_den = 25000000
WHERE loai = 'po' AND vai_tro_id = (SELECT id FROM vai_tro WHERE ma = 'TP_CU');
UPDATE han_muc_duyet SET nguong_tu = 25000001
WHERE loai = 'po' AND vai_tro_id = (SELECT id FROM vai_tro WHERE ma = 'CEO');
