.PHONY: db-up db-down setup seed run test reset
db-up:        ## Bật PostgreSQL (docker) + tự nạp schema/seed lần đầu
	docker compose up -d db
db-down:      ## Tắt DB (giữ dữ liệu)
	docker compose down
reset:        ## Xoá sạch DB rồi tạo lại từ đầu
	docker compose down -v && docker compose up -d db
setup:        ## Tạo venv + cài thư viện
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
seed:         ## Tạo 13 user demo (mật khẩu matkhau123)
	python -m scripts.tao_user_demo
run:          ## Chạy API (http://localhost:8000/docs)
	uvicorn app.main:app --reload
test:         ## Chạy test đầu-cuối (cần DB đang chạy)
	pytest -q
