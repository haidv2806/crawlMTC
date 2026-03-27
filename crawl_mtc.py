# crawl_mtc.py - Crawler metruyenchu.co
#
# Usage:
#   python crawl_mtc.py --url https://metruyenchu.co/truyen/<slug>
#   python crawl_mtc.py --pages 2 --sort totalViews
#   python crawl_mtc.py --url https://... --limit 5   (giới hạn 5 chương đầu)
#
# Tính năng:
#   1. Proxy rotation (round-robin, không cần CloudFlare bypass)
#   2. Crawl chapters trong volume song song (asyncio.gather)
#   3. Skip sách đã crawl (skip_books.json)
#   4. Retry vô hạn khi gặp 429 (đợi 60s)

import argparse
import asyncio
import json
import os
import tempfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from core.config import (
    BASE_URL, CHAPTERS_PER_VOLUME, HEADERS,
    MTC_BASE, MTC_HEADERS,
    should_skip_book, add_skip_book,
    get_next_proxy,
)
from core.mtc_categories import map_tags
from scrapers.mtc_book import download_cover, parse_book_info
from scrapers.mtc_chapters import get_chapters
from scrapers.mtc_chapter_content import get_chapter_content_async

# Rate limit: 100 req/min => đợi 60s khi gặp 429
RATE_LIMIT_WAIT = 60


# ------------------------------------------------------------------ #
# Lấy danh sách URL truyện từ /danh-sach                              #
# ------------------------------------------------------------------ #

def fetch_book_list(page: int = 1, sort: str = "totalViews") -> list[str]:
    """
    Tải trang danh sách MTC và trả về list URL truyện.
    URL: https://metruyenchu.co/danh-sach?page=N&sort=...
    """
    url = f"{MTC_BASE}/danh-sach"
    params = {"page": str(page), "sort": sort}
    try:
        proxy = get_next_proxy()
        resp = requests.get(url, params=params, headers=MTC_HEADERS, proxies=proxy, timeout=30)
        soup = BeautifulSoup(resp.text, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/truyen/") and href.count("/") == 2:
                full = MTC_BASE + href
                if full not in seen:
                    seen.add(full)
                    urls.append(full)
        return urls
    except Exception as e:
        print(f"[search] Lỗi trang {page}: {e}")
        return []


# ------------------------------------------------------------------ #
# Backend API calls                                                    #
# ------------------------------------------------------------------ #

def _backend_post(url: str, **kwargs) -> requests.Response:
    """
    POST lên backend (localhost:3000) với retry 429 vô hạn.
    Không dùng proxy cho local backend.
    """
    import time
    while True:
        try:
            resp = requests.post(url, headers=HEADERS, timeout=60, **kwargs)
            if resp.status_code == 429:
                print(f"  [backend] 429 Rate Limit. Đợi {RATE_LIMIT_WAIT}s...")
                time.sleep(RATE_LIMIT_WAIT)
                continue
            return resp
        except Exception as e:
            print(f"  [backend] Lỗi: {e}. Thử lại sau 5s...")
            time.sleep(5)


def api_create_book(info: dict, cover_path: str) -> int | None:
    """Tạo sách trên backend. Trả về backend book_id."""
    url = f"{BASE_URL}/Book/create"
    categories = map_tags(info.get("tags", []))
    data = [
        ("book_name",   info["name"]),
        ("sub_names",   json.dumps(info.get("sub_names", []), ensure_ascii=False)),
        ("authors",     json.dumps(info["authors"], ensure_ascii=False)),
        ("status",      info["status"]),
        ("description", (info.get("description") or "")[:1000]),
    ]
    for cat_id in categories:
        data.append(("categories[]", str(cat_id)))

    try:
        with open(cover_path, "rb") as img_f:
            ext = Path(cover_path).suffix or ".jpg"
            files = {"image": (f"cover{ext}", img_f, "image/jpeg")}
            resp = _backend_post(url, data=data, files=files)
        print(f"  [book] create: {resp.status_code} | {resp.text[:200]}")
        if resp.status_code not in (200, 201):
            return None
        return resp.json().get("data", {}).get("book_id")
    except Exception as e:
        print(f"  [book] Lỗi: {e}")
        return None


def api_create_volume(book_id: int, volume_name: str) -> int | None:
    """Tạo volume. Trả về volume_id."""
    url = f"{BASE_URL}/Book/Volume/create"
    resp = _backend_post(
        url,
        json={"book_id": book_id, "volume_name": volume_name, "status": "completed"},
    )
    print(f"  [vol] {volume_name}: {resp.status_code}")
    if resp.status_code not in (200, 201):
        return None
    data = resp.json().get("data")
    if data and isinstance(data, dict):
        return data.get("volume_id")
    return resp.json().get("volume_id") or resp.json().get("id")


def api_create_chapter(volume_id: int, chapter_name: str, content: str) -> bool:
    """Upload chương dạng .md lên backend."""
    url = f"{BASE_URL}/Book/Volume/Chapter/create"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False
    ) as f:
        f.write(content)
        tmp = f.name

    result = False
    try:
        data = {
            "volume_id":    str(volume_id),
            "chapter_name": chapter_name,
            "status":       "completed",
        }
        with open(tmp, "rb") as md_f:
            files = {"markdownFile": ("chapter.md", md_f, "text/markdown")}
            resp = _backend_post(url, data=data, files=files)
        result = resp.status_code in (200, 201)
    except Exception as e:
        print(f"  [chap] Lỗi API: {e}")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return result


# ------------------------------------------------------------------ #
# Helper                                                              #
# ------------------------------------------------------------------ #

def default_cover_path() -> str:
    for base in [Path(__file__).parent, Path(__file__).parent.parent]:
        p = base / "defaultImage.png"
        if p.exists():
            return str(p)
    return str(Path(__file__).parent / "defaultImage.png")


# ------------------------------------------------------------------ #
# Parallel chapter crawl across volumes (same position)               #
# ------------------------------------------------------------------ #

async def _crawl_and_upload_chapter(
    idx: int,
    total: int,
    ch: dict,
    volume_id: int,
) -> None:
    """Crawl 1 chương và upload lên backend."""
    ch_url   = ch["url"]
    ch_title = ch.get("name") or f"Chương {idx}"

    result = await get_chapter_content_async(ch_url)
    if not result.get("ok"):
        print(f"  [{idx}/{total}] Lỗi: {result.get('error')} — {ch_url}")
        return

    content = result.get("content", "")
    if not content:
        print(f"  [{idx}/{total}] Nội dung trống, bỏ qua.")
        return

    chap_name = result.get("title") or ch_title
    success   = api_create_chapter(volume_id, chap_name, content)
    status    = "OK" if success else "FAIL"
    print(f"  [{idx}/{total}] {status}: {str(chap_name)[:60]}")


# ------------------------------------------------------------------ #
# Core crawl logic                                                     #
# ------------------------------------------------------------------ #

async def crawl_book(
    book_url: str,
    chapter_limit: int | None = None,
):
    """
    Crawl 1 cuốn sách:
      0. Skip nếu đã crawl trước đó
      1. Lấy thông tin sách → ảnh bìa → tạo sách backend
      2. Lấy danh sách chương
      3. Tạo THẤT CẢ volume tuần tự (sequential)
      4. Sau đó cào song song theo hàng ngang:
         - cào chương đầu tiên của mỗi volume đồng thời
         - rồi chương thứ 2 của mỗi volume đồng thời
         - v.v... (giống hresizable "heatmap" theo cột)
      5. Thêm vào skip list sau khi thành công
    Ví dụ 1000 chương (10 vol):
      - Vừng 1: tạo vol1..vol10 (sequential)
      - Vừng 2: crawl ch1(v1)+ch101(v2)+ch201(v3)+...+ch901(v10) cùng lúc
                  crawl ch2(v1)+ch102(v2)+ch202(v3)+...+ch902(v10) cùng lúc
                  ...
    """
    print(f"\n{'='*60}")
    print(f"[book] {book_url}")

    # 0. Skip nếu đã crawl
    if should_skip_book(book_url):
        print(f"  [skip] Bỏ qua (đã crawl trước đó): {book_url}")
        return

    # 1. Lấy thông tin sách
    info = parse_book_info(book_url)
    if not info:
        print("  [book] Không lấy được thông tin, bỏ qua.")
        return

    book_slug = info.get("book_slug", "")
    book_id   = info.get("book_id", "")
    print(f"  [book] {info['name']} | slug={book_slug} | id={book_id}")

    if not book_slug:
        print("  [book] Không có book_slug, bỏ qua.")
        return

    # 2. Lấy danh sách chương
    if not book_id:
        print("  [book] Không detect được book_id từ HTML, Playwright sẽ tự bắt từ request...")

    chapters = await get_chapters(book_url, book_slug)
    if not chapters:
        print("  [book] Không có chương nào, bỏ qua.")
        return

    if chapter_limit:
        chapters = chapters[:chapter_limit]
    print(f"  [book] {len(chapters)} chương sẽ crawl")

    # 3. Tải ảnh bìa
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        cover_path = f.name
    ok = download_cover(info.get("cover_url", ""), cover_path)
    if not ok:
        if os.path.exists(cover_path):
            os.remove(cover_path)
        cover_path = default_cover_path()

    # 4. Tạo sách trên backend
    backend_book_id = api_create_book(info, cover_path)
    if cover_path != default_cover_path() and os.path.exists(cover_path):
        os.remove(cover_path)
    if not backend_book_id:
        print("  [book] Không tạo được sách, bỏ qua.")
        return
    print(f"  [book] Đã tạo sách backend_book_id={backend_book_id}")

    # 5. Chia chunk thành các volume
    total = len(chapters)
    volumes: list[dict] = []   # [{"name": ..., "volume_id": ..., "chapters": [...]}]

    for vol_start in range(0, total, CHAPTERS_PER_VOLUME):
        chunk    = chapters[vol_start : vol_start + CHAPTERS_PER_VOLUME]
        vol_end  = vol_start + len(chunk)
        vol_name = f"Chương {vol_start + 1} - {vol_end}"

        # Tạo volume tuần tự
        volume_id = api_create_volume(backend_book_id, vol_name)
        if not volume_id:
            print(f"  [vol] Không tạo được volume {vol_name}, bỏ qua.")
            continue

        volumes.append({
            "name":      vol_name,
            "volume_id": volume_id,
            "chapters":  chunk,
            "offset":    vol_start,   # global chapter index offset
        })

    if not volumes:
        print("  [book] Không tạo được bất kỳ volume nào.")
        return

    print(f"  [vol] Đã tạo {len(volumes)} volume. Bắt đầu cào chương song song theo hàng ngang...")

    # 6. Tời đa số chương trong 1 volume
    max_chapters_in_vol = max(len(v["chapters"]) for v in volumes)

    # 7. Cào các chương song song theo hàng ngang (không giới hạn concurrency)
    #    Row i: ch[i] của mọi volume được crawl đồng thời
    for row in range(max_chapters_in_vol):
        row_tasks = []
        for vol in volumes:
            if row >= len(vol["chapters"]):
                continue   # volume này ít chương hơn
            ch        = vol["chapters"][row]
            global_idx = vol["offset"] + row + 1
            row_tasks.append(
                _crawl_and_upload_chapter(
                    idx=global_idx,
                    total=total,
                    ch=ch,
                    volume_id=vol["volume_id"],
                )
            )
        if row_tasks:
            await asyncio.gather(*row_tasks)

    # 8. Thêm vào skip list sau khi crawl xong
    add_skip_book(book_url)
    print(f"  [book] ✅ Hoàn thành: {info['name']}")


# ------------------------------------------------------------------ #
# Main                                                                 #
# ------------------------------------------------------------------ #

async def main():
    parser = argparse.ArgumentParser(description="Crawler metruyenchu.co")
    parser.add_argument("--url",        type=str, default=None,
                        help="URL 1 cuốn sách cụ thể")
    parser.add_argument("--start-page", type=int, default=1,
                        help="Trang bắt đầu trong danh sách (mặc định: 1)")
    parser.add_argument("--pages",      type=int, default=1,
                        help="Trang kết thúc (inclusive). Ví dụ: --start-page 2 --pages 5 sẽ crawl trang 2–5")
    parser.add_argument("--sort",       type=str, default="totalViews",
                        help="Sắp xếp danh sách: totalViews | updatedAt | ...")
    parser.add_argument("--limit",      type=int, default=None,
                        help="Giới hạn số chương mỗi sách (dùng để test)")
    args = parser.parse_args()

    start_page = args.start_page
    end_page   = max(args.pages, start_page)   # pages giờ là trang kết thúc

    if args.url:
        # Crawl 1 sách cụ thể
        await crawl_book(args.url, args.limit)
    else:
        # Crawl theo danh sách từ start_page đến end_page
        seen: set[str] = set()
        for page in range(start_page, end_page + 1):
            print(f"\n[search] Trang {page} (từ {start_page} đến {end_page})...")
            urls = fetch_book_list(page=page, sort=args.sort)
            print(f"[search] Tìm thấy {len(urls)} truyện trang {page}")
            for url in urls:
                if url in seen:
                    continue
                seen.add(url)
                await crawl_book(url, args.limit)


if __name__ == "__main__":
    asyncio.run(main())
