# scrapers/mtc_book.py
# Lấy thông tin sách và tải ảnh bìa từ metruyenchu.co

import re
from bs4 import BeautifulSoup
from pathlib import Path

from core.config import MTC_BASE
from core.req_config import proxy_get


def parse_book_info(book_url: str) -> dict | None:
    """
    Lấy thông tin sách từ trang truyện MTC.
    Trả về dict: name, authors, status, tags, cover_url, description, book_slug, book_id
    """
    try:
        resp = proxy_get(book_url)
        if resp.status_code != 200:
            print(f"  [book] HTTP {resp.status_code} khi GET {book_url}")
            return None
        html = resp.text
    except Exception as e:
        print(f"  [book] Lỗi request: {e}")
        return None

    soup = BeautifulSoup(html, "html.parser")

    # --- Tên truyện ---
    name = ""
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)

    if not name:
        print("  [book] Không lấy được tên sách.")
        return None

    # --- Tác giả ---
    author_a = soup.find("a", href=lambda x: x and "/tac-gia/" in x)
    authors = [author_a.get_text(strip=True)] if author_a else ["Không rõ"]

    # --- Trạng thái ---
    status = "ongoing"
    ul_tags = soup.find("ul", class_=lambda c: c and "flex-wrap" in c)
    if ul_tags:
        status_div = ul_tags.find("div", class_=lambda c: c and "border-primary" in c)
        if status_div:
            raw = status_div.get_text(strip=True).lower()
            if "hoàn" in raw or "complete" in raw:
                status = "completed"

    # --- Thể loại ---
    genres = []
    if ul_tags:
        for a_tag in ul_tags.find_all("a", href=lambda x: x and "/danh-sach/" in x):
            genres.append(a_tag.get_text(strip=True))

    # --- Ảnh bìa ---
    cover_url = ""
    og_image = soup.find("meta", property="og:image")
    if og_image:
        cover_url = og_image.get("content", "")
    if not cover_url:
        img = soup.find("img", class_=lambda c: c and "object-cover" in c)
        if img:
            cover_url = img.get("src", "")

    # --- Mô tả ---
    description = ""
    desc_tag = soup.find("div", class_=lambda c: c and "prose" in c)
    if desc_tag:
        lines = [ln.strip() for ln in desc_tag.get_text().split("\n")]
        description = "\n".join(ln for ln in lines if ln)

    # --- Lấy book_slug và book_id (MongoDB) ---
    # URL dạng: https://metruyenchu.co/truyen/<slug>
    slug_match = re.search(r"/truyen/([^/?#]+)", book_url)
    book_slug = slug_match.group(1) if slug_match else ""

    # book_id thường nằm trong meta tag hoặc script JSON-LD
    book_id = _extract_book_id(soup, book_slug)

    return {
        "name": name,
        "authors": authors,
        "status": status,
        "tags": genres,
        "cover_url": cover_url,
        "description": description,
        "book_slug": book_slug,
        "book_id": book_id,   # MongoDB _id dùng cho chapter list API
    }


def _extract_book_id(soup: BeautifulSoup, book_slug: str) -> str:
    """
    Extract MongoDB book ID từ HTML.
    MTC nhúng book_id trong đường dẫn ảnh bìa hoặc inline JSON arrays.
    """
    # 1. Tìm trong URL ảnh bìa (id 24 ký tự)
    cover_meta = soup.find("meta", property="og:image")
    if cover_meta:
        m = re.search(r'cover/([0-9a-f]{24})', cover_meta.get("content", ""))
        if m: return m.group(1)
        
    img = soup.find("img", class_=lambda c: c and "object-cover" in c)
    if img:
        m = re.search(r'cover/([0-9a-f]{24})', img.get("src", ""))
        if m: return m.group(1)

    page_text = str(soup)
    
    # 2. Tìm pattern inline JSON: "695...","name":"Toan Cau..."
    m = re.search(r'"([0-9a-f]{24})","name":"', page_text)
    if m: return m.group(1)

    # 3. Tìm trong bất kỳ đoạn text nào có hex 24 ký tự gần slug
    pattern = rf'"{re.escape(book_slug)}"[^{{}}]*?"([0-9a-f]{{24}})"'
    m = re.search(pattern, page_text)
    if m:
        return m.group(1)

    # 4. Tìm bất kỳ chuỗi hex 24 ký tự đầu tiên (fallback)
    m = re.search(r'"([0-9a-f]{24})"', page_text)
    if m:
        return m.group(1)

    return ""


def download_cover(cover_url: str, save_path: str) -> bool:
    """
    Tải ảnh bìa về file tạm. Trả về True nếu thành công.
    """
    if not cover_url:
        return False
    try:
        resp = proxy_get(cover_url)
        if resp.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return True
        print(f"  [cover] HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"  [cover] Lỗi tải ảnh: {e}")
        return False
