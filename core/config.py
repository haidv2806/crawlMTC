# core/config.py
# Cấu hình dùng chung cho crawler MTC (metruyenchu.co)

# ================== BACKEND API ==================
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJqdGkiOiJiNTE3N2NmNC00Yzc0LTRjZTUtYmI4OS00Y2Q1MTMzNDBkZmIiLCJpYXQiOjE3NzQ0NzM3NzUsImV4cCI6MTc3NzA2NTc3NX0.RZ9l_GjS3nNPgLUBkbodpx_V-KtanLPkBtg2JHT4REA"

BASE_URL = "http://localhost:3000"
# BASE_URL = "https://e-books.info.vn"

HEADERS = {
    "Authorization": f"Bearer {JWT_TOKEN}"
}

# ================== MTC SITE ==================
MTC_BASE = "https://metruyenchu.co"

# ================== CRAWL CONFIG ==================
CHAPTERS_PER_VOLUME = 100   # Mỗi volume chứa tối đa 100 chương

# ================== REQUEST HEADERS (cho MTC site) ==================
MTC_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}
