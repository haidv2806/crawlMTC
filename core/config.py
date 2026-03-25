# core/config.py
# Cấu hình dùng chung cho crawler MTC (metruyenchu.co)

import json
from pathlib import Path

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

# ================== PROXY ROTATION ==================
# Đọc proxy từ file proxies.txt (format mỗi dòng: ip:port:username:password)
_PROXIES_FILE = Path(__file__).parent.parent / "proxies.txt"

def _load_raw_proxies() -> list[str]:
    if not _PROXIES_FILE.exists():
        return []
    lines = _PROXIES_FILE.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and ":" in l]

raw_proxies = _load_raw_proxies()


def _parse_proxy(proxy_str: str) -> dict:
    """Parse 'ip:port:user:pass' thành dict proxy cho requests."""
    parts = proxy_str.split(":")
    ip, port, user, pwd = parts[0], parts[1], parts[2], parts[3]
    proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
    return {
        "http": proxy_url,
        "https": proxy_url,
    }


PROXIES = [_parse_proxy(p) for p in raw_proxies]
_proxy_index = 0


def get_next_proxy() -> dict | None:
    """
    Round-robin qua danh sách proxy.
    Trả về dict {"http": ..., "https": ...} hoặc None nếu không có proxy.
    """
    global _proxy_index
    if not PROXIES:
        return None
    proxy = PROXIES[_proxy_index]
    _proxy_index = (_proxy_index + 1) % len(PROXIES)
    return proxy


# ================== SKIP BOOKS MANAGEMENT ==================
SKIP_BOOKS_FILE = Path(__file__).parent.parent / "skip_books.json"
_skip_books: set = set()
_skip_books_loaded = False


def _load_skip_books():
    global _skip_books, _skip_books_loaded
    if SKIP_BOOKS_FILE.exists():
        try:
            with open(SKIP_BOOKS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _skip_books = set(data.get("urls", []))
        except Exception as e:
            print(f"⚠️ Lỗi load skip_books.json: {e}")
            _skip_books = set()
    else:
        _skip_books = set()
    _skip_books_loaded = True


def _save_skip_books():
    try:
        with open(SKIP_BOOKS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"urls": sorted(_skip_books), "count": len(_skip_books)},
                f, indent=2, ensure_ascii=False
            )
    except Exception as e:
        print(f"⚠️ Lỗi save skip_books.json: {e}")


def should_skip_book(url: str) -> bool:
    """Kiểm tra xem URL sách có trong danh sách skip không."""
    global _skip_books_loaded
    if not _skip_books_loaded:
        _load_skip_books()
    return url in _skip_books


def add_skip_book(url: str):
    """Thêm URL sách vào danh sách skip sau khi crawl thành công."""
    global _skip_books_loaded
    if not _skip_books_loaded:
        _load_skip_books()
    if url not in _skip_books:
        _skip_books.add(url)
        _save_skip_books()
        print(f"  [skip] Đã thêm vào skip list: {url}")


# Load skip books khi khởi động
_load_skip_books()
