import json
import sys
from bs4 import BeautifulSoup

def extract_book_details(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Tên truyện
    title_tag = soup.find('h1')
    title = title_tag.text.strip() if title_tag else "N/A"

    # 2. Tên tác giả
    author_tag = soup.find('a', href=lambda x: x and '/tac-gia/' in x)
    author = author_tag.text.strip() if author_tag else "N/A"

    # 3. Link hình ảnh
    img_tag = soup.find('meta', property='og:image')
    if img_tag:
        img_link = img_tag['content']
    else:
        cover_img = soup.find('img', class_=lambda c: c and 'object-cover' in c)
        img_link = cover_img['src'] if cover_img else "N/A"

    # 4. Giới thiệu
    desc_tag = soup.find('div', class_=lambda c: c and 'prose' in c)
    if desc_tag:
        lines = [line.strip() for line in desc_tag.text.split('\n')]
        description = '\n'.join([line for line in lines if line])
    else:
        description = "N/A"

    # 5. Phân tích Thể loại và Trạng thái
    genres = []
    status = "N/A"
    
    ul_tags = soup.find('ul', class_=lambda c: c and 'flex-wrap' in c)
    if ul_tags:
        status_div = ul_tags.find('div', class_=lambda c: c and 'border-primary' in c)
        if status_div:
            status = status_div.text.strip()
            
        for a_tag in ul_tags.find_all('a', href=lambda x: x and '/danh-sach/' in x):
            genres.append(a_tag.text.strip())

    book_info = {
        "TenTruyen": title,
        "TacGia": author,
        "TrangThai": status,
        "TheLoai": genres,
        "LinkHinhAnh": img_link,
        "GioiThieu": description
    }

    return book_info

if __name__ == "__main__":
    file_path = r"f:\crawlSTV\crawlMTC\Abook.html"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        book_info = extract_book_details(html_content)
        
        # In trực tiếp ra console dạng JSON
        print(json.dumps(book_info, ensure_ascii=False, indent=4))
        
    except FileNotFoundError:
        print(json.dumps({"error": f"Không tìm thấy file {file_path}"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
