-- 106: phieu thu chi nho lenh ngan hang da sinh ra no (de mo lai lenh khi phieu bi tu choi/huy)
ALTER TABLE phieu_thu_chi ADD COLUMN IF NOT EXISTS lenh_chi_id BIGINT;
