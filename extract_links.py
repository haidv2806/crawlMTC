import requests
from bs4 import BeautifulSoup

def extract_story_links_from_html(html_content):
    """
    Trích xuất các link truyện từ nội dung HTML của trang danh sách.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    
    # Tìm tất cả các thẻ <a> có href bắt đầu bằng '/truyen/'
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('/truyen/'):
            full_link = f"https://metruyenchu.co{href}"
            links.add(full_link)
            
    return sorted(list(links))

def fetch_html_from_url(url):
    """
    Tải nội dung HTML từ URL bằng thư viện requests với Headers giả lập trình duyệt.
    Lưu ý: Nếu trang dùng Cloudflare, bạn có thể cần dùng tls_client hoặc FlareSolverr.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8'
    }
    
    print(f"Đang tải dữ liệu từ {url}...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

if __name__ == "__main__":
    import sys
    
    # Bản mặc định sẽ tải từ URL trực tiếp
    use_local_file = False  # Thay đổi thành True nếu muốn tải từ file cục bộ
    
    story_links = []
    
    if use_local_file:
        file_path = r"f:\crawlSTV\crawlMTC\srearch.html"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            story_links = extract_story_links_from_html(html_content)
            print(f"Đã đọc file nội bộ: {file_path}")
        except FileNotFoundError:
            print(f"Không tìm thấy file {file_path}. Vui lòng kiểm tra lại đường dẫn.")
            sys.exit(1)
    else:
        # Ví dụ tải từ một URL cụ thể
        url = "https://metruyenchu.co/danh-sach?page=1&sort=totalViews"
        try:
            html_content = fetch_html_from_url(url)
            story_links = extract_story_links_from_html(html_content)
        except Exception as e:
            print(f"Lỗi khi tải URL: {e}")
            sys.exit(1)
    
    print(f"\nTìm thấy {len(story_links)} link truyện duy nhất:")
    for i, link in enumerate(story_links, 1):
        print(f"{i}. {link}")
