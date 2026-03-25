# Mê Truyện Chữ (MTC) Link Extractor

Dự án này giúp trích xuất link truyện từ trang danh sách của Metruyenchu.co.

## Hướng dẫn cài đặt

Để cài đặt và chạy script, bạn hãy mở terminal tại thư mục này và thực hiện các bước sau:

### 1. Tạo môi trường ảo (Virtual Environment)
```bash
python -m venv myenv
```

### 2. Kích hoạt môi trường ảo
Trên Windows:
```bash
myenv\Scripts\activate
```

### 3. Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

## Hướng dẫn sử dụng

### Trích xuất link truyện
Chạy script `extract_links.py` để lấy danh sách link truyện:
```bash
python extract_links.py
```

*Lưu ý: Mặc định script sẽ đọc từ file `srearch.html`. Nếu bạn muốn tải trực tiếp từ URL, hãy mở file `extract_links.py` và sửa `use_local_file = False`.*

## Các file trong dự án
- `extract_links.py`: Script chính để trích xuất link.
- `requirements.txt`: Danh sách các thư viện cần thiết.
- `srearch.html`: File HTML mẫu để trích xuất dữ liệu.
- `map_categories.py`: Script hỗ trợ mapping thể loại truyện.
