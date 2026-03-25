# scrapers/mtc_chapters.py
# Lấy danh sách chương từ metruyenchu.co
#
# MTC dùng Next.js Server Actions:
#   POST <book_url>
#   Header: Next-Action: <hash>
#   Body: [{"bookId": "...", "page": 1, "limit": 10000, "isNewest": false}]
#   Response: text/x-component (RSC payload chứa JSON)
#
# Hash được detect tự động bằng Playwright (intercept network requests).

import re
import json
import asyncio
from playwright.async_api import async_playwright

from core.config import MTC_BASE, MTC_HEADERS
from core.req_config import proxy_post


# ------------------------------------------------------------------ #
# Playwright: detect next-action hash                                  #
# ------------------------------------------------------------------ #

async def detect_action_hash(book_url: str) -> tuple[str, str]:
    """
    Dùng Playwright để mở trang và bắt next-action hash cùng book_id từ request.
    Trả về tuple (hash, book_id). Nếu thất bại trả về ("", "").
    """
    print(f"  [hash] Đang detect hash từ: {book_url}")
    hashes = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=MTC_HEADERS["User-Agent"]
            )
            page = await context.new_page()

            async def intercept(route):
                request = route.request
                if "next-action" in request.headers and request.method == "POST":
                    body = request.post_data or ""
                    hashes.append({
                        "hash": request.headers.get("next-action"),
                        "body": body,
                    })
                await route.continue_()

            await page.route("**/*", intercept)
            await page.goto(book_url, wait_until="networkidle", timeout=30000)

            # Click "Mục Lục" để trigger chapter list request
            try:
                await page.click("text=Mục Lục", timeout=10000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  [hash] Không click được 'Mục Lục': {e}")

            await browser.close()
    except Exception as e:
        print(f"  [hash] Lỗi Playwright: {e}")
        return "", ""

    # Lấy hash có body chứa "bookId" (chapter list request)
    for h in hashes:
        if "bookId" in h["body"] and "page" in h["body"]:
            print(f"  [hash] Phát hiện hash: {h['hash']}")
            # Trích xuất bookId từ body (dạng [{"bookId":"xxx",...}])
            book_id_match = re.search(r'"bookId"\s*:\s*"([a-fA-F0-9]+)"', h["body"])
            book_id = book_id_match.group(1) if book_id_match else ""
            if book_id:
                print(f"  [hash] Bắt được book_id: {book_id}")
            return h["hash"], book_id

    # Fallback: trả hash đầu tiên nếu có chứa bookId
    for h in hashes:
        if "bookId" in h["body"]:
            print(f"  [hash] Dùng hash (fallback): {h['hash']}")
            book_id_match = re.search(r'"bookId"\s*:\s*"([a-fA-F0-9]+)"', h["body"])
            book_id = book_id_match.group(1) if book_id_match else ""
            return h["hash"], book_id

    return "", ""


# ------------------------------------------------------------------ #
# Parse RSC payload                                                    #
# ------------------------------------------------------------------ #

def parse_chapters_from_rsc(rsc_text: str, book_slug: str) -> list[dict]:
    """
    Parse danh sách chương từ React Server Component payload.
    Pattern: {"_id":"...","slugId":"chuong-XXX","number":N,"bookId":"...","name":"Chương N:..."}
    """
    chapters = []
    pattern = (
        r'\{"_id":"[^"]+","slugId":"(chuong-[^"]+)",'
        r'"number":(\d+),"bookId":"[^"]+","name":"([^"]+)"'
    )
    matches = re.findall(pattern, rsc_text)
    for slug, number, name in matches:
        chapters.append({
            "slug": slug,
            "number": int(number),
            "name": name,
            "url": f"{MTC_BASE}/truyen/{book_slug}/{slug}",
        })
    return chapters


# ------------------------------------------------------------------ #
# Fetch chapters via Server Action                                     #
# ------------------------------------------------------------------ #

def _build_rsc_headers(book_url: str, book_slug: str, action_hash: str) -> dict:
    return {
        **MTC_HEADERS,
        "Accept": "text/x-component",
        "Origin": MTC_BASE,
        "Referer": book_url,
        "Content-Type": "text/plain;charset=UTF-8",
        "Next-Action": action_hash,
        "Next-Router-State-Tree": (
            "%5B%22%22%2C%7B%22children%22%3A%5B%22truyen%22%2C%7B%22children%22%3A"
            "%5B%5B%22id%22%2C%22" + book_slug + "%22%2C%22d%22%5D%2C%7B%22children"
            "%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D"
        ),
    }


def fetch_all_chapters(
    book_id: str,
    book_url: str,
    action_hash: str,
    book_slug: str,
) -> list[dict]:
    """
    Lấy toàn bộ chương bằng 1 POST request (limit=10000).
    Fallback sang phân trang nếu cần.
    """
    print(f"  [chapters] Đang lấy danh sách chương (1 request)...")
    headers = _build_rsc_headers(book_url, book_slug, action_hash)
    body = json.dumps([{
        "bookId": book_id,
        "page": 1,
        "limit": 10000,
        "isNewest": False,
    }])

    try:
        resp = proxy_post(book_url, headers=headers, data=body, use_proxy=True)
        print(f"  [chapters] Status: {resp.status_code}, Size: {len(resp.text)} chars")
        if resp.status_code != 200:
            return []
        chapters = parse_chapters_from_rsc(resp.text, book_slug)
        if chapters:
            print(f"  [chapters] Parse được {len(chapters)} chương")
            return chapters
    except Exception as e:
        print(f"  [chapters] Lỗi: {e}")

    # Fallback: phân trang
    print("  [chapters] Thử phân trang...")
    return fetch_chapters_paginated(book_id, book_url, action_hash, book_slug)


def fetch_chapters_paginated(
    book_id: str,
    book_url: str,
    action_hash: str,
    book_slug: str,
    limit: int = 200,
) -> list[dict]:
    """Lấy chương theo từng trang (fallback)."""
    all_chapters: list[dict] = []
    headers = _build_rsc_headers(book_url, book_slug, action_hash)
    page: int = 1

    while True:
        print(f"  [chapters] Trang {page}...")
        body = json.dumps([{
            "bookId": book_id,
            "page": page,
            "limit": limit,
            "isNewest": False,
        }])
        try:
            resp = proxy_post(book_url, headers=headers, data=body, use_proxy=True)
        except Exception as e:
            print(f"  [chapters] Lỗi trang {page}: {e}")
            break

        if resp.status_code != 200:
            break
        chapters = parse_chapters_from_rsc(resp.text, book_slug)
        if not chapters:
            break
        all_chapters.extend(chapters)
        print(f"  [chapters]   → {len(chapters)} chương, tổng: {len(all_chapters)}")
        if len(chapters) < limit:
            break
        page += 1

    return all_chapters


# ------------------------------------------------------------------ #
# Main entry                                                           #
# ------------------------------------------------------------------ #

async def get_chapters(book_url: str, book_slug: str) -> list[dict]:
    """
    Hàm chính: detect hash & bookId → fetch chapters → sort + dedup.
    """
    action_hash, real_book_id = await detect_action_hash(book_url)
    if not action_hash or not real_book_id:
        print("  [chapters] Không detect được hash hoặc bookId, bỏ qua.")
        return []

    chapters = fetch_all_chapters(real_book_id, book_url, action_hash, book_slug)

    if not chapters:
        return []

    # Sort và loại trùng
    chapters.sort(key=lambda x: x["number"])
    seen: set[int] = set()
    unique: list[dict] = []
    for ch in chapters:
        if ch["number"] not in seen:
            unique.append(ch)
            seen.add(ch["number"])

    print(f"  [chapters] Tổng {len(unique)} chương duy nhất")
    return unique
