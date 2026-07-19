from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://svws:svws@localhost:5432/svws"
    jwt_secret: str = "doi-secret-nay-trong-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30 * 24 * 60   # 30 ngày — "ghi nhớ đăng nhập" trên trình duyệt

    # Lưu trữ tệp (PO/Hợp đồng). Prod: trỏ sang mount S3/MinIO.
    storage_dir: str = "./storage"
    # Email gateway: DEMO (ghi log) | SMTP. Prod: điền SMTP/SendGrid.
    email_provider: str = "DEMO"
    email_from: str = "sv-sales@watersolutions.company"
    email_from_ncc: str = "inf@watersolutions.company"   # 1 đầu mối mua hàng / NCC
    email_cc_bao_gia: str = "sv-hieu@watersolutions.company"  # CC tự động khi gửi báo giá
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

    # ---- Google Chat (Work Reminder) ----
    # DEMO   : không gửi thật, chỉ ghi log (mặc định — an toàn)
    # APP    : Chat app + Service Account -> NHẮN RIÊNG từng người (cần Workspace admin)
    # WEBHOOK: đăng vào một Phòng chung qua Incoming Webhook (setup 5 phút)
    chat_provider: str = "DEMO"
    gchat_webhook_url: str = ""          # dùng cho chế độ WEBHOOK
    gchat_service_account: str = ""      # dùng cho chế độ APP: DÁN NGUYÊN nội dung file JSON key
    nhac_viec_gui_khi_tao: bool = True   # gửi ngay khi vừa đặt lời nhắc
    nhac_viec_ban_tin: bool = True       # bản tin tổng hợp đầu ngày
    nhac_viec_gio_ban_tin: int = 8       # giờ gửi bản tin (0-23, GIỜ VIỆT NAM)
    # Máy chủ Render chạy giờ UTC nhưng người dùng nhập giờ Việt Nam, và cột
    # thoi_diem/han_hoan_thanh lưu giờ địa phương -> phải quy đổi khi so sánh.
    tz_offset_gio: int = 7               # UTC+7


settings = Settings()
