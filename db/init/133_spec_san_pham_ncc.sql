-- 133: San pham NCC — cot SPEC (thong so ky thuat) AI doc tu email / file bao gia / datasheet; bao gia email co LOAI
ALTER TABLE san_pham_ncc ADD COLUMN IF NOT EXISTS spec TEXT;
ALTER TABLE san_pham_ncc ADD COLUMN IF NOT EXISTS spec_nguon VARCHAR(160);
ALTER TABLE san_pham_ncc ADD COLUMN IF NOT EXISTS spec_luc TIMESTAMP;
ALTER TABLE bg_email_cho ADD COLUMN IF NOT EXISTS loai VARCHAR(12) DEFAULT 'BAO_GIA';
