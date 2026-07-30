-- Tài liệu kỹ thuật chia 3 nhóm: Nước cấp - Siêu sạch | Nước thải | Khí thải
ALTER TABLE dich_vu_kt_tai_lieu ADD COLUMN IF NOT EXISTS nhom varchar(20);
-- Tự phân loại tài liệu hiện có theo từ khóa trong tên (đổi lại được trên app)
UPDATE dich_vu_kt_tai_lieu SET nhom='KHI_THAI'
 WHERE nhom IS NULL AND (ten ILIKE '%khí%' OR ten ILIKE '%khi thai%' OR ten ILIKE '%exhaust%'
                         OR ten ILIKE '%flue%' OR ten ILIKE '%scrubber%');
UPDATE dich_vu_kt_tai_lieu SET nhom='NUOC_THAI'
 WHERE nhom IS NULL AND (ten ILIKE '%thải%' OR ten ILIKE '%nuoc thai%' OR ten ILIKE '%wwtp%'
                         OR ten ILIKE '%wastewater%' OR ten ILIKE '%mbr%' OR ten ILIKE '%aao%');
UPDATE dich_vu_kt_tai_lieu SET nhom='NUOC_CAP_SS' WHERE nhom IS NULL;
