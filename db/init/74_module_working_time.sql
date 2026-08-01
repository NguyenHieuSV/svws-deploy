-- Module quyền RIÊNG cho Working time & Report (tách khỏi nhan_su).
-- Seed ban đầu: copy đúng mức hiện tại của cột nhan_su → không ai bị đứt quyền;
-- CEO chỉnh tiếp trong ma trận Phân quyền.
INSERT INTO phan_quyen (vai_tro_id, module, muc)
SELECT p.vai_tro_id, 'working_time', p.muc
FROM phan_quyen p
WHERE p.module = 'nhan_su'
  AND NOT EXISTS (SELECT 1 FROM phan_quyen q
                  WHERE q.vai_tro_id = p.vai_tro_id AND q.module = 'working_time');
