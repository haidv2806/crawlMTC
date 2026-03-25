# scrapers/mtc_chapter_content.py
# Lấy nội dung chương từ metruyenchu.co và chuyển sang dạng Markdown

import re
from bs4 import BeautifulSoup

from core.req_config import proxy_get_async


async def get_chapter_content_async(chapter_url: str) -> dict:
    """
    Async: Tải trang chương và trả về nội dung dạng Markdown.
    Dùng proxy rotation + retry 429 tự động qua proxy_get_async.

    Trả về:
        {
            "ok": True/False,
            "title": "Tên chương",
            "content": "Nội dung markdown...",
            "error": "..."   # chỉ khi ok=False
        }
    """
    try:
        resp = await proxy_get_async(chapter_url)
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
        title = raw_title.replace("::", ":").replace(": :", ": ")
    title = re.sub(r"\s*:\s*", ": ", title)

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

    lines: list[str] = []
    if chapter_title:
        lines.append(f"# {chapter_title}\n")
    lines.extend(paragraphs)

    return "\n\n".join(lines)
