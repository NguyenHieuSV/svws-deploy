-- 153 — Công ty đổi trụ sở (19/10/2026): Tầng 14, Toà nhà HM Town, 412 Nguyễn Thị Minh Khai, P. Bàn Cờ, TP.HCM.
-- Bản mô tả công việc (JD) của TP_QLNB và CEO có câu «Địa điểm: trụ sở 448 Võ Văn Tần ...» lưu trong mo_ta_cong_viec.yeu_cau.
-- Chỉ thay đúng cụm địa chỉ cũ, giữ nguyên phần còn lại (kể cả chỗ đã chỉnh tay). Chạy lại nhiều lần vẫn an toàn.
UPDATE mo_ta_cong_viec
SET yeu_cau = REPLACE(REPLACE(yeu_cau,
        'trụ sở 448 Võ Văn Tần, P. Bàn Cờ, TP.HCM', 'trụ sở Tầng 14, Toà nhà HM Town, 412 Nguyễn Thị Minh Khai, P. Bàn Cờ, TP.HCM'),
        'trụ sở 448 Võ Văn Tần, Q.3, TP.HCM', 'trụ sở Tầng 14, Toà nhà HM Town, 412 Nguyễn Thị Minh Khai, P. Bàn Cờ, TP.HCM')
WHERE yeu_cau LIKE '%448 Võ Văn Tần%';
