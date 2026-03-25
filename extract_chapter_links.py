"""
Script lấy toàn bộ danh sách chương từ metruyenchu.co
Sử dụng Next.js Server Actions

Cơ chế hoạt động:
- Website dùng Next.js Server Actions (không phải REST API thông thường)
- Khi click "Mục Lục" → trang phân trang, browser gửi POST đến URL truyện
- Header: next-action: <hash>   (hash có thể đổi khi website deploy mới)
- Body: [{"bookId": "...", "page": 1, "limit": 1000000000, "isNewest": false}]
- Response: text/x-component (React Server Component payload, chứa JSON)

Hash tự động được detect từ trang bằng Playwright lần đầu,
sau đó dùng requests để gọi thẳng không cần browser.
"""
import re
import asyncio
import json
import requests
from playwright.async_api import async_playwright

BOOK_SLUG = "toan-cau-than-tuyen-bat-dau-lua-chon-phong-do-dai-de"
BOOK_ID = "696447c38dd3bd60781c7b6b"
BASE_URL = "https://metruyenchu.co"
BOOK_URL = f"{BASE_URL}/truyen/{BOOK_SLUG}"

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/x-component",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    "Origin": BASE_URL,
    "Referer": BOOK_URL,
    "Content-Type": "text/plain;charset=UTF-8",
    "Next-Router-State-Tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22truyen%22%2C%7B%22children%22%3A%5B%5B%22id%22%2C%22" + BOOK_SLUG + "%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
}


async def detect_action_hashes(book_url: str, book_slug: str) -> dict:
    """
    Dùng Playwright để tự động detect next-action hashes từ trang.
    Trả về dict: {
        "chapter_list_hash": hash để lấy danh sách chương (có pagination),
        "modal_open_hash": hash khi mở modal lần đầu
    }
    """
    print(f"[*] Đang detect hashes từ {book_url}...")
    hashes = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS_BASE["User-Agent"]
        )
        page = await context.new_page()
        
        async def intercept(route):
            request = route.request
            if "next-action" in request.headers and request.method == "POST":
                hashes.append({
                    "hash": request.headers.get("next-action"),
                    "body": request.post_data or "",
                })
            await route.continue_()
        
        await page.route("**/*", intercept)
        await page.goto(book_url, wait_until="networkidle", timeout=30000)
        
        # Click Mục Lục
        try:
            await page.click("text=Mục Lục", timeout=10000)
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  [Warn] {e}")
        
        # Click phân trang (trang 2) để lấy hash pagination
        try:
            await page.click("button[aria-label='2'], button:has-text('2')", timeout=3000)
            await page.wait_for_timeout(2000)
        except:
            pass
        
        await browser.close()
    
    result = {}
    for h in hashes:
        body = h["body"]
        if "page" in body and "limit" in body:
            result["chapter_list_hash"] = h["hash"]
            print(f"  [✓] chapter_list_hash: {h['hash']}")
            print(f"      body mẫu: {body[:100]}")
        elif body.startswith('["'):
            result["modal_open_hash"] = h["hash"]
            print(f"  [✓] modal_open_hash: {h['hash']}")
    
    return result


def fetch_all_chapters(book_id: str, book_url: str, action_hash: str, book_slug: str) -> list:
    """
    Gửi POST request trực tiếp để lấy toàn bộ chương.
    Dùng limit=10000 để lấy tất cả một lần.
    """
    print(f"\n[*] Đang lấy toàn bộ chương (1 request)...")
    
    headers = {**HEADERS_BASE, "Next-Action": action_hash}
    body = json.dumps([{
        "bookId": book_id,
        "page": 1,
        "limit": 10000,
        "isNewest": False
    }])
    
    response = requests.post(book_url, headers=headers, data=body, timeout=60)
    
    print(f"  Status: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('content-type', '')}")
    print(f"  Response size: {len(response.text)} chars")
    print(f"  Preview: {response.text[:300]}")
    
    if response.status_code != 200:
        print(f"  [Error] HTTP {response.status_code}")
        return []
    
    return parse_chapters_from_rsc(response.text, book_slug)


def parse_chapters_from_rsc(rsc_text: str, book_slug: str) -> list:
    """
    Parse danh sách chương từ React Server Component payload.
    RSC format: các dòng JSON stream, chứa data object với chapters array.
    """
    chapters = []
    
    # Tìm tất cả JSON objects có slugId bắt đầu với "chuong-"
    # Pattern: {"_id":"...","slugId":"chuong-XXX","number":N,"bookId":"...","name":"Chương N:..."}
    pattern = r'\{"_id":"[^"]+","slugId":"(chuong-[^"]+)","number":(\d+),"bookId":"[^"]+","name":"([^"]+)"'
    matches = re.findall(pattern, rsc_text)
    
    for slug, number, name in matches:
        chapters.append({
            "slug": slug,
            "number": int(number),
            "name": name,
            "url": f"https://metruyenchu.co/truyen/{book_slug}/{slug}",
        })
    
    return chapters


def fetch_chapters_paginated(book_id: str, book_url: str, action_hash: str, book_slug: str, total: int = 1116) -> list:
    """
    Phương án dự phòng: lấy chương theo từng trang nếu không lấy được 1 lần.
    """
    all_chapters = []
    page = 1
    limit = 200
    
    while True:
        print(f"  [*] Trang {page}...")
        headers = {**HEADERS_BASE, "Next-Action": action_hash}
        body = json.dumps([{
            "bookId": book_id,
            "page": page,
            "limit": limit,
            "isNewest": False
        }])
        
        response = requests.post(book_url, headers=headers, data=body, timeout=30)
        if response.status_code != 200:
            break
        
        chapters = parse_chapters_from_rsc(response.text, book_slug)
        if not chapters:
            break
        
        all_chapters.extend(chapters)
        print(f"    → {len(chapters)} chương, tổng: {len(all_chapters)}")
        
        if len(all_chapters) >= total:
            break
        page += 1
    
    return all_chapters


async def main():
    print("=" * 60)
    print("CRAWL DANH SÁCH CHƯƠNG - METRUYENCHU.CO")
    print("=" * 60)
    print(f"Truyện: {BOOK_SLUG}")
    print(f"URL: {BOOK_URL}\n")
    
    # Bước 1: Detect hashes
    hashes = await detect_action_hashes(BOOK_URL, BOOK_SLUG)
    
    if not hashes.get("chapter_list_hash"):
        print("\n[!] Không detect được hash, dùng hash đã biết...")
        # Fallback hash đã detect trước đó
        hashes["chapter_list_hash"] = "401b9ba455c4a6d34a47eb6d95d05184eaff298633"
    
    action_hash = hashes["chapter_list_hash"]
    
    # Bước 2: Lấy tất cả chương một lần
    chapters = fetch_all_chapters(BOOK_ID, BOOK_URL, action_hash, BOOK_SLUG)
    
    # Bước 3: Nếu không parse được, thử phân trang
    if not chapters:
        print("\n[!] Không lấy được bằng 1 request, thử phân trang...")
        chapters = fetch_chapters_paginated(BOOK_ID, BOOK_URL, action_hash, BOOK_SLUG)
    
    if chapters:
        chapters.sort(key=lambda x: x["number"])
        # Loại bỏ duplicate
        seen = set()
        unique_chapters = []
        for ch in chapters:
            if ch["number"] not in seen:
                unique_chapters.append(ch)
                seen.add(ch["number"])
        chapters = unique_chapters
        
        print(f"\n{'='*60}")
        print(f"[✓] Lấy được {len(chapters)} chương!")
        print(f"{'='*60}")
        print(f"\n5 chương đầu:")
        for ch in chapters[:5]:
            print(f"  [{ch['number']:4d}] {ch['name'][:60]}")
        print(f"\n5 chương cuối:")
        for ch in chapters[-5:]:
            print(f"  [{ch['number']:4d}] {ch['name'][:60]}")
        
        # Lưu URLs vào file
        output_urls = f"f:\\crawlSTV\\crawlMTC\\chapter_urls_{BOOK_SLUG}.txt"
        with open(output_urls, "w", encoding="utf-8") as f:
            for ch in chapters:
                f.write(ch["url"] + "\n")
        print(f"\n[✓] Đã lưu {len(chapters)} URLs vào: {output_urls}")
        
        # Lưu JSON đầy đủ
        output_json = f"f:\\crawlSTV\\crawlMTC\\chapters_{BOOK_SLUG}.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)
        print(f"[✓] Đã lưu JSON đầy đủ vào: {output_json}")
    else:
        print("\n[✗] Không lấy được chương nào!")
        print("  Nguyên nhân có thể:")
        print("  1. Hash đã thay đổi (website deploy mới)")
        print("  2. Cloudflare chặn request")
        print("  3. Response format thay đổi")


asyncio.run(main())
