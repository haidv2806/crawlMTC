import json
import sys
from bs4 import BeautifulSoup

def extract_chapter_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    
    for a_tag in soup.find_all('a', href=lambda x: x and '/truyen/' in x and '/chuong-' in x):
        href = a_tag['href']
        full_link = f"https://metruyenchu.co{href}" if href.startswith('/') else href
        
        if full_link not in links:
            links.append(full_link)
            
    return links

if __name__ == "__main__":
    file_path = r"f:\crawlSTV\crawlMTC\Abook.html"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        chapter_links = extract_chapter_links(html_content)
        
        # In trực tiếp ra console dạng JSON
        print(json.dumps(chapter_links, ensure_ascii=False, indent=4))
            
    except FileNotFoundError:
        print(json.dumps({"error": f"Không tìm thấy file {file_path}"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
