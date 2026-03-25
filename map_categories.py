# stv_categories.py - Mapping tag sangtacviet.app → category_id trong DB
# Tất cả truyện đều mặc định có Chinese Novel (ID=10)

# Bảng mapping: keyword (lowercase, không dấu hay có một phần) → category_id
# Tìm theo "contains" để xử lý biến thể tên tag

CHINESE_NOVEL_ID = 10  # Mặc định tất cả đều là Chinese Novel

# Map: fragment (lower) → category_id
# Một tag STV có thể map vào nhiều category
_KEYWORD_MAP = [
    # Action (1)
    ("hanh dong", 1),
    ("nhiet huyet", 1),
    ("chien dau", 1),
    ("chien than", 1),
    ("vo thuat", 1),
    ("sang van", 1),
    ("nhanh tiet tau", 1),
    ("sat phat qua doan", 1),
    ("vo dich", 1),

    # Adapted to Anime (2)
    ("anime dien sinh", 2),
    ("chuyen the anime", 2),
    ("anime", 2),

    # Adapted to Manga (4)
    ("chuyen the manga", 4),
    ("manhua", 4),
    ("dien sinh", 4), # Thường là diễn sinh anime/manga

    # Adult (5)
    ("18+", 5),
    ("nguoi lon", 5),
    ("hen", 5),       
    ("nhi thu nguyen", 5), # Đôi khi mang nghĩa Otaku/Adult

    # Adventure (6)
    ("mao hiem", 6),
    ("tham hiem", 6),
    ("phieu luu", 6),
    ("chu thien", 6),
    ("sinh ton", 6),
    ("hai tac", 6),

    # Age Gap (7)
    ("chenh lech giai cap", 7),

    # Boys Love (8)
    ("dam my", 8),
    ("ngon dam", 8),
    ("song nam chinh", 8),

    # Character Growth (9)
    ("truong thanh", 9),
    ("nhan vat truong thanh", 9),
    ("thien tai", 9),
    ("thang cap", 9),
    ("xay dung the luc", 9),
    ("thang cap luu", 9),
    ("pham nhan luu", 9),

    # Comedy (11)
    ("hai huoc", 11),
    ("khoi hai", 11),
    ("ham cuoi", 11),
    ("vo si", 11),
    ("choi nganh", 11),
    ("xau bung", 11),
    ("nhe nhom", 11),

    # Cooking (12)
    ("nau an", 12),
    ("am thuc", 12),
    ("my thuc", 12),

    # Different Social Status (13)
    ("hao mon", 13),

    # Drama (14)
    ("chinh kich", 14),
    ("nguoi o re", 14),
    ("trong sinh", 14),
    ("trung sinh", 14),

    # Ecchi (15)
    ("ecchi", 15),

    # Fantasy (17)
    ("huyen huyen", 17),
    ("ky huyen", 17),
    ("ki huyen", 17),
    ("ky ao", 17),
    ("di the", 17),
    ("di gioi", 17),
    ("huyen tuong", 17),
    ("long", 17),
    ("tay huyen", 17),

    # Female Protagonist (18)
    ("nu chinh", 18),
    ("nu ton", 18),
    ("nu de", 18),

    # Game (19)
    ("vong du", 19),
    ("tro choi", 19),
    ("game", 19),

    # Gender Bender (20)
    ("bien than", 20),
    ("sfacg", 20),

    # Harem (21)
    ("hau cung", 21),
    ("harem", 21),
    ("nhieu nu chinh", 21),

    # Historical (22)
    ("lich su", 22),
    ("co dai", 22),
    ("da su", 22),
    ("gia khong lich su", 22),
    ("quan truong", 22),

    # Horror (23)
    ("kinh di", 23),
    ("kinh khung", 23),
    ("linh di", 23),
    ("quy di", 23),
    ("mat the", 23),
    ("tan the", 23),

    # Incest (24)
    ("loan luan", 24),

    # Isekai (25)
    ("xuyen qua", 25),
    ("xuyen khong", 25),
    ("isekai", 25),
    ("xuyen thu", 25),
    ("nhanh xuyen", 25),

    # Magic (28)
    ("ma phap", 28),
    ("phap thuat", 28),

    # Martial Arts (29)
    ("vo hiep", 29),
    ("luyen cong", 29),
    ("tien hiep", 29),
    ("tu tien", 29),
    ("kiem hiep", 29),
    ("cao vo", 29),
    ("co dien tien hiep", 29),
    ("vo dao", 29),

    # Mature (30)
    ("truong thanh", 30),
    ("lanh khoc", 30),

    # Military (32)
    ("quan su", 32),
    ("quan doi", 32),
    ("thiet huyet", 32),

    # Mystery (34)
    ("huyen nghi", 34),
    ("trinh tham", 34),
    ("bi an", 34),
    ("quy bi", 34),
    ("doi song", 34),

    # Parody (38)
    ("dong nhan", 38),
    ("fan fiction", 38),
    ("tong man", 38),

    # Psychological (39)
    ("tam ly", 39),
    ("co tri", 39),
    ("tri dau", 39),
    ("giao hoat", 39),
    ("phan phai", 39),
    ("sau man", 39),
    ("nao dong lon", 39),

    # Romance (41)
    ("ngon tinh", 41),
    ("tinh yeu", 41),
    ("tinh cam", 41),
    ("hon nhan", 41),
    ("ngot sung", 41),
    ("thuan ai", 41),
    ("don nu chinh", 41),

    # School Life (42)
    ("hoc duong", 42),
    ("san truong", 42),
    ("vuon truong", 42),
    ("hoc ba", 42),

    # Science Fiction (43)
    ("khoa huyen", 43),
    ("khoa hoc vien tuong", 43),
    ("tuong lai", 43),
    ("khong gian", 43),
    ("tinh te", 43),
    ("thoi khong", 43),

    # Shounen (47)
    ("nam sinh", 47),
    ("goc nhin nam", 47),

    # Slice of Life (49)
    ("do thi", 49),
    ("sinh hoat", 49),
    ("cuoc song", 49),
    ("thuong ngay", 49),
    ("toan dan", 49),
    ("nhe nhang", 49),

    # Slow Life (50)
    ("diem van", 50),
    ("nhan ha", 50),
    ("lam ruong", 50),
    ("dien vien", 50),
    ("ca man", 50),

    # Sports (51)
    ("the thao", 51),
    ("bong da", 51),
    ("bong chuyen", 51),
    ("the duc", 51),
    ("canh ky", 51),

    # Super Power (52)
    ("di nang", 52),
    ("sieu nang luc", 52),
    ("sieu anh hung", 52),
    ("ngu thu", 52),
    ("sung vat", 52),
    ("tien hoa", 52),

    # Supernatural (53)
    ("than bi", 53),
    ("than thoai", 53),
    ("linh khi khoi phuc", 53),
    ("he thong", 53),
    ("tuy than", 53),

    # Tragedy (55)
    ("bi kich", 55),
    ("tham kich", 55),

    # Wars (56)
    ("chien tranh", 56),
    ("tranh ba", 56),

    # Web Novel (57)
    ("light novel", 57),

    # Workplace (58)
    ("cong so", 58),
    ("van phong", 58),
    ("thuong chien", 58),
    ("kinh doanh", 58),

    # Yuri (59)
    ("bach hop", 59),
    ("yuri", 59),
    ("chi em yeu nhau", 59),
    ("dong tinh nu", 59),
]


def _remove_diacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt để match keyword."""
    import unicodedata
    if not text:
        return ""
    # Chuyển sang dạng NFD rồi bỏ combining diacritical marks
    normalized = unicodedata.normalize('NFD', text.lower().strip())
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')


def map_tags(tag_list: list[str]) -> list[int]:
    """
    Chuyển list tag STV → list category_id.
    Luôn bao gồm CHINESE_NOVEL_ID (10).
    Bỏ qua tag không map được (không fallback).
    Dùng Set nên sẽ không có ID bị trùng lặp.
    """
    result = {CHINESE_NOVEL_ID}  # Mặc định Chinese Novel

    for tag in tag_list:
        tag_clean = _remove_diacritics(tag)
        for keyword, cat_id in _KEYWORD_MAP:
            keyword_clean = _remove_diacritics(keyword)
            if keyword_clean in tag_clean:
                result.add(cat_id)
                break  # Mỗi keyword map lấy cái đầu tiên khớp với tag string đó

    return sorted(list(result))


if __name__ == "__main__":
    # Test
    test_tags = ["Huyền Huyễn", "Xuyên Qua", "Ngôn Tình", "Hệ Thống", "blah unknown"]
    print("Tags:", test_tags)
    print("Category IDs:", map_tags(test_tags))
