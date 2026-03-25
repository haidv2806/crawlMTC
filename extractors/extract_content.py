import sys
import json
import requests
from bs4 import BeautifulSoup

def extract_chapter(url_or_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    html_content = ""
    # Nếu là URL HTTP/HTTPS
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        try:
            # Thử dùng cloudscraper trước để bypass Cloudflare nếu có
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url_or_path, headers=headers)
            if response.status_code != 200:
                return {"error": f"Failed to fetch {url_or_path}, status: {response.status_code}"}
            html_content = response.text
        except ImportError:
            # Fallback dùng requests thường
            response = requests.get(url_or_path, headers=headers)
            if response.status_code != 200:
                return {"error": f"Failed to fetch {url_or_path}, status: {response.status_code}"}
            html_content = response.text
    else:
        # Đọc từ file local
        try:
            with open(url_or_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception as e:
            return {"error": f"Failed to read local file: {e}"}

    soup = BeautifulSoup(html_content, "html.parser")
    
    # 1. Tên truyện
    story_name = ""
    h1_tag = soup.find("h1")
    if h1_tag:
        story_name = h1_tag.get_text(strip=True)
        
    # 2. Nội dung chapter
    content = ""
    article = soup.find("article")
    if article:
        paragraphs = article.find_all("p")
        # Kết hợp các đoạn văn lại, mỗi đoạn cách nhau 1 dòng trống
        content = "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        
    # Tạo object kết quả
    result = {
        "story_name": story_name,
        "content": content
    }
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Sử dụng: python extract_content.py <URL hoặc Đường_dẫn_file>")
        print("Ví dụ: python extract_content.py https://metruyenchu.co/truyen/...")
        sys.exit(1)
        
    input_str = sys.argv[1]
    output_data = extract_chapter(input_str)
    
    # In ra output là JSON format chuẩn
    print(json.dumps(output_data, ensure_ascii=False, indent=4))
