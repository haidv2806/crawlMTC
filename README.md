# Mê Truyện Chữ (MTC) Crawler

Cào truyện từ metruyenchu.co: tạo sách, chia volume (100 chương/vol), tải ảnh bìa, upload chương dạng `.md` lên backend server.

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
├── extractors/              # Các extractor cũ (giữ nguyên)
├── crawl_mtc.py             # 🚀 Script chính
├── map_categories.py        # Mapping cũ (giữ nguyên)
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
- `JWT_TOKEN`: Token xác thực backend
- `BASE_URL`: URL backend server

## Sử dụng

### Crawl 1 truyện cụ thể

```bash
python crawl_mtc.py --url https://metruyenchu.co/truyen/<slug>
```

### Crawl với giới hạn chương (để test)

```bash
python crawl_mtc.py --url https://metruyenchu.co/truyen/<slug> --limit 5
```

### Crawl danh sách truyện (nhiều trang)

```bash
python crawl_mtc.py --pages 2 --sort totalViews
```

### Tham số dòng lệnh

| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `--url` | — | URL truyện cụ thể |
| `--pages` | `1` | Số trang danh sách cần crawl |
| `--sort` | `totalViews` | Sắp xếp: `totalViews`, `updatedAt` |
| `--limit` | — | Giới hạn số chương mỗi sách |

## Cơ chế hoạt động

1. **Lấy danh sách truyện**: Tải trang `/danh-sach` và parse link truyện
2. **Lấy thông tin sách**: Parse tên, tác giả, thể loại, ảnh bìa từ trang truyện
3. **Detect next-action hash**: Dùng Playwright để bắt hash Next.js Server Action
4. **Lấy danh sách chương**: Gửi POST request trực tiếp với hash vừa detect
5. **Tạo sách trên backend**: `POST /Book/create` kèm ảnh bìa
6. **Tạo volume**: Mỗi 100 chương tạo 1 volume (`POST /Book/Volume/create`)
7. **Upload chương**: Nội dung parse thành Markdown → `POST /Book/Volume/Chapter/create`
