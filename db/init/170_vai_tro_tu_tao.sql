-- 170 — 🪪 CEO TỰ TẠO VỊ TRÍ / CHỨC DANH (anh Hiếu 16/11/2026): bảng tạo người dùng ở Cấu hình chỉ có droplist vị trí
--       cố định (seed 02 / 25 / 73) → thêm cột đánh dấu vị trí do CEO tạo trong app (đổi tên / xóa được), ghi chú, giờ tạo.
--       Vị trí seed sẵn giữ tu_tao = FALSE: mã của chúng được dùng trong code (chi_vai_tro("KTT","CEO")…) nên không
--       đổi tên / không xóa. Logic: app/vi_tri.py · API /cau-hinh/vai-tro (POST / PATCH / DELETE chỉ CEO).
ALTER TABLE vai_tro ADD COLUMN IF NOT EXISTS tu_tao  BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE vai_tro ADD COLUMN IF NOT EXISTS ghi_chu VARCHAR(300);
ALTER TABLE vai_tro ADD COLUMN IF NOT EXISTS tao_luc TIMESTAMP;
