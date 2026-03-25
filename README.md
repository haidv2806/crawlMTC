# Mê Truyện Chữ (MTC) Crawler

Cào truyện từ `metruyenchu.co`: tạo sách, chia volume (100 chương/vol), tải ảnh bìa, upload chương dạng `.md` lên backend server.

## Cấu trúc dự án

```
crawlMTC/
├── core/
│   ├── config.py            # Cấu hình: JWT, BASE_URL, MTC_BASE, headers
│   └── mtc_categories.py    # Mapping thể loại → category_id
├── scrapers/
│   ├── mtc_book.py          # Lấy thông tin sách & ảnh bìa
│   ├── mtc_chapters.py      # Detect next-action hash + lấy danh sách chương
│   └── mtc_chapter_content.py  # Lấy nội dung chương → Markdown
├── proxies.txt              # Danh sách Proxy (Định dạng ip:port:user:pass)
├── skip_books.json          # Danh sách URL sách đã crawl xong (tự động tạo)
├── crawl_mtc.py             # 🚀 Script chính
└── requirements.txt
```

## Cài đặt

```bash
# Tạo và kích hoạt môi trường ảo
python -m venv myenv
myenv\Scripts\activate

# Cài thư viện
pip install -r requirements.txt

# Cài Playwright browsers (cần cho lần đầu)
playwright install chromium
```

## Cấu hình

Mở `core/config.py` và cập nhật:
- `JWT_TOKEN`: Token xác thực backend.
- `BASE_URL`: URL backend server (Ví dụ: `https://e-books.info.vn`).

### Quản lý Proxy
Tạo hoặc chỉnh sửa file `proxies.txt` ở thư mục gốc. Mỗi dòng là một proxy với định dạng:
`ip:port:username:password`

Dự án sẽ tự động đọc danh sách này và xoay vòng (round-robin) khi gửi request tới MTC.

## Sử dụng

### Crawl 1 truyện cụ thể

```bash
python crawl_mtc.py --url https://metruyenchu.co/truyen/<slug>
```

### Crawl danh sách truyện theo trang

Mặc định, crawler sẽ lấy thông tin từ danh sách truyện. Bạn có thể chỉ định khoảng trang cần crawl.

```bash
# Crawl từ trang 1 đến trang 2
python crawl_mtc.py --pages 2 --sort totalViews

# Crawl từ trang 5 đến trang 10
python crawl_mtc.py --start-page 5 --pages 10

# Crawl chỉ trang 2
python crawl_mtc.py --start-page 2 --pages 2
```

### Tham số dòng lệnh

| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `--url` | — | URL truyện cụ thể |
| `--start-page` | `1` | Trang bắt đầu trong danh sách |
| `--pages` | `1` | Trang kết thúc (inclusive). Ví dụ: `--start-page 2 --pages 5` sẽ crawl trang 2–5 |
| `--sort` | `totalViews` | Sắp xếp: `totalViews`, `updatedAt`, ... |
| `--limit` | — | Giới hạn số chương mỗi sách (dùng để test) |

## Cơ chế hoạt động

1. **Lấy danh sách truyện**: Tải trang `/danh-sach` và parse link truyện.
2. **Lấy thông tin sách**: Parse tên, tác giả, thể loại, ảnh bìa từ trang truyện.
3. **Detect next-action hash**: Dùng Playwright để bắt hash Next.js Server Action.
4. **Lấy danh sách chương**: Gửi POST request trực tiếp với hash vừa detect.
5. **Proxy Rotation**: Tự động xoay vòng danh sách proxy từ `proxies.txt` để tránh bị chặn IP.
6. **Concurrency**: Cào chương song song theo hàng ngang (mỗi volume một chương đồng thời) không giới hạn luồng để đạt tốc độ tối đa.
7. **Tạo sách trên backend**: `POST /Book/create` kèm ảnh bìa.
8. **Tạo volume**: Mỗi 100 chương tạo 1 volume (`POST /Book/Volume/create`).
9. **Upload chương**: Nội dung parse thành Markdown → `POST /Book/Volume/Chapter/create`.
10. **Skip List**: Sách đã crawl thành công sẽ được lưu vào `skip_books.json` để tránh crawl lặp lại.
