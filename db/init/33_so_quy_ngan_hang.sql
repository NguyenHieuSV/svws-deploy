-- Bốn sổ quỹ chuẩn cho Thống kê thu chi: Vietcombank - BIDV - Đông Á - Tiền mặt
INSERT INTO tai_khoan_quy (ma, ten, loai, tk_ke_toan, so_du_dau, so_du, hoat_dong)
SELECT 'VCB', 'Vietcombank', 'NGAN_HANG', '112', 0, 0, TRUE
WHERE NOT EXISTS (SELECT 1 FROM tai_khoan_quy WHERE ma = 'VCB' OR ten ILIKE '%vietcombank%');

INSERT INTO tai_khoan_quy (ma, ten, loai, tk_ke_toan, so_du_dau, so_du, hoat_dong)
SELECT 'BIDV', 'BIDV', 'NGAN_HANG', '112', 0, 0, TRUE
WHERE NOT EXISTS (SELECT 1 FROM tai_khoan_quy WHERE ma = 'BIDV' OR ten ILIKE '%bidv%');

INSERT INTO tai_khoan_quy (ma, ten, loai, tk_ke_toan, so_du_dau, so_du, hoat_dong)
SELECT 'DONGA', 'Đông Á', 'NGAN_HANG', '112', 0, 0, TRUE
WHERE NOT EXISTS (SELECT 1 FROM tai_khoan_quy WHERE ma = 'DONGA' OR ten ILIKE '%đông á%' OR ten ILIKE '%dong a%');

INSERT INTO tai_khoan_quy (ma, ten, loai, tk_ke_toan, so_du_dau, so_du, hoat_dong)
SELECT 'TM', 'Tiền mặt', 'TIEN_MAT', '111', 0, 0, TRUE
WHERE NOT EXISTS (SELECT 1 FROM tai_khoan_quy WHERE ma = 'TM' OR loai = 'TIEN_MAT');
