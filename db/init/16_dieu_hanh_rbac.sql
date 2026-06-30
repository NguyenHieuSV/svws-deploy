-- ============================================================
-- SVWS — Quyền tab 'Overall Operation' (module dieu_hanh)
-- CEO mặc định có quyền QUAN_TRI (vừa truy cập vừa là người DUYỆT).
-- Các vị trí khác: KHÔNG (chờ CEO duyệt qua UI -> POST /cau-hinh/dieu-hanh/duyet).
-- Idempotent: chạy lại an toàn.
-- ============================================================
BEGIN;

INSERT INTO phan_quyen (vai_tro_id, module, muc)
SELECT vt.id, 'dieu_hanh', 'QUAN_TRI'::muc_quyen
FROM vai_tro vt
WHERE vt.ma = 'CEO'
ON CONFLICT (vai_tro_id, module) DO UPDATE SET muc = EXCLUDED.muc;

COMMIT;
