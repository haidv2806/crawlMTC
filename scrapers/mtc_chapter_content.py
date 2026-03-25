# scrapers/mtc_chapter_content.py
# Lấy nội dung chương từ metruyenchu.co và chuyển sang dạng Markdown

import requests
from bs4 import BeautifulSoup
import re

from core.config import MTC_HEADERS


def get_chapter_content(chapter_url: str) -> dict:
    """
    Tải trang chương và trả về nội dung dạng Markdown.

    Trả về:
        {
            "ok": True/False,
            "title": "Tên chương",
            "content": "Nội dung markdown...",
            "error": "..."   # chỉ khi ok=False
        }
    """
    try:
        resp = requests.get(chapter_url, headers=MTC_HEADERS, timeout=60)
        if resp.status_code != 200:
            return {"ok": False, "error": f"HTTP {resp.status_code}"}
        html = resp.text
    except Exception as e:
        return {"ok": False, "error": str(e)}

    soup = BeautifulSoup(html, "html.parser")

    # --- Tên chương ---
    title = ""

    span = soup.find("span", class_="text-neutral-400")
    if span:
        raw_title = span.get_text(strip=True)
        # Xử lý trường hợp có "::" hoặc ": :" thành ": "
        title = raw_title.replace("::", ":").replace(": :", ": ")
    
    # Nếu vẫn muốn loại bỏ khoảng trắng thừa quanh dấu :
    title = re.sub(r'\s*:\s*', ': ', title)

    # Hoặc cách ngắn gọn hơn (nếu chỉ có 1 span kiểu này):
    # title = soup.find("span", {"class": "text-neutral-400"}).get_text(strip=True) if soup.find("span", {"class": "text-neutral-400"}) else ""

    # --- Nội dung ---
    content_md = _extract_content(soup, title)

    if not content_md:
        return {"ok": False, "error": "Nội dung trống"}

    return {"ok": True, "title": title, "content": content_md}


def _extract_content(soup: BeautifulSoup, chapter_title: str) -> str:
    """
    Extract nội dung từ <article> hoặc các div chứa nội dung chương.
    Chuyển mỗi <p> thành 1 đoạn văn Markdown (cách nhau 1 dòng trống).
    """
    paragraphs: list[str] = []

    # Ưu tiên tìm trong <article>
    article = soup.find("article")
    source = article if article else soup

    # Thử các selector phổ biến của MTC
    content_div = (
        source.find("div", class_=lambda c: c and "chapter-content" in c)
        or source.find("div", class_=lambda c: c and "prose" in c)
        or source.find("section", class_=lambda c: c and "content" in c)
        or article
    )

    if content_div:
        for p in content_div.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)
    elif article:
        # Fallback: tất cả text trong article
        for p in article.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

    if not paragraphs:
        return ""

    # Tạo Markdown: tiêu đề + nội dung
    lines: list[str] = []
    if chapter_title:
        lines.append(f"# {chapter_title}\n")
    lines.extend(paragraphs)

    return "\n\n".join(lines)
