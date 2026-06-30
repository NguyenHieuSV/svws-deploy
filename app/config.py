from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://svws:svws@localhost:5432/svws"
    jwt_secret: str = "doi-secret-nay-trong-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 8 * 60

    # Lưu trữ tệp (PO/Hợp đồng). Prod: trỏ sang mount S3/MinIO.
    storage_dir: str = "./storage"
    # Email gateway: DEMO (ghi log) | SMTP. Prod: điền SMTP/SendGrid.
    email_provider: str = "DEMO"
    email_from: str = "sv-sales@watersolutions.company"
    email_from_ncc: str = "inf@watersolutions.company"   # 1 đầu mối mua hàng / NCC
    cong_ty_ten: str = "CÔNG TY TNHH GPKT SÓNG VIỆT"
    cong_ty_slogan: str = "We Have Solutions"
    cong_ty_dia_chi: str = "448 Võ Văn Tần, P. Bàn Cờ, Q.3, Tp. HCM"
    cong_ty_tel: str = "(084) 937120039"
    cong_ty_email: str = "info@watersolutions.company"
    cong_ty_website: str = "watersolutions.company"
    pdf_font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    pdf_font_bold_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    pdf_chu_ky_path: str = ""   # ảnh chữ ký/đóng dấu (tùy chọn)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    # Cổng thư đến (thu thư phản hồi): DEMO | IMAP
    inbound_provider: str = "DEMO"
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_pass: str = ""
    # Cổng AI phân loại thư: DEMO (luật) | ANTHROPIC
    ai_provider: str = "DEMO"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    auto_tim_ncc: bool = False          # tự chạy AI Sourcing khi đề xuất được duyệt
    auto_cham_diem_ncc: bool = True     # tự chấm điểm NCC sau khi nhận đủ hàng
    web_search_tool: str = "web_search_20250305"  # công cụ tìm NCC mới trên web
    # Tự gửi email XÁC NHẬN ĐÃ NHẬN cho nhóm ý định an toàn (mặc định tắt; nội dung cố định, vẫn tạo việc cho người)
    auto_tra_loi: bool = False
    auto_tra_loi_ydinh: str = "QUAN_TAM,HOI_KY_THUAT,HEN_GAP"


settings = Settings()
