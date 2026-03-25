# core/mtc_categories.py
# Mapping thể loại MTC (metruyenchu.co) → category_id trong DB backend
# Mặc định tất cả truyện đều có Chinese Novel (ID=10)

CHINESE_NOVEL_ID = 10

# Map: từ khóa (không dấu, viết thường) → category_id
_KEYWORD_MAP = [
    # Action (1)
    ("hanh dong", 1),
    ("nhiet huyet", 1),
    ("chien dau", 1),
    ("chien than", 1),
    ("vo thuat", 1),
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
    ("dien sinh", 4),

    # Adult (5)
    ("18+", 5),
    ("nguoi lon", 5),
    ("hen tai", 5),

    # Adventure (6)
    ("mao hiem", 6),
    ("tham hiem", 6),
    ("phieu luu", 6),
    ("chu thien", 6),
    ("sinh ton", 6),

    # Boys Love (8)
    ("dam my", 8),
    ("ngon dam", 8),

    # Character Growth (9)
    ("truong thanh nhan vat", 9),
    ("thien tai", 9),
    ("thang cap", 9),
    ("xay dung the luc", 9),

    # Comedy (11)
    ("hai huoc", 11),
    ("khoi hai", 11),
    ("nhe nhom", 11),

    # Cooking (12)
    ("nau an", 12),
    ("am thuc", 12),
    ("my thuc", 12),

    # Drama (14)
    ("trong sinh", 14),
    ("trung sinh", 14),

    # Fantasy (17)
    ("huyen huyen", 17),
    ("ky huyen", 17),
    ("ky ao", 17),
    ("di the", 17),
    ("di gioi", 17),
    ("huyen tuong", 17),
    ("tay huyen", 17),

    # Female Protagonist (18)
    ("nu chinh", 18),
    ("nu ton", 18),

    # Game (19)
    ("vong du", 19),
    ("tro choi", 19),
    ("game", 19),

    # Harem (21)
    ("hau cung", 21),
    ("harem", 21),

    # Historical (22)
    ("lich su", 22),
    ("co dai", 22),
    ("quan truong", 22),

    # Horror (23)
    ("kinh di", 23),
    ("linh di", 23),
    ("tan the", 23),

    # Isekai (25)
    ("xuyen qua", 25),
    ("xuyen khong", 25),
    ("isekai", 25),
    ("xuyen thu", 25),

    # Magic (28)
    ("ma phap", 28),
    ("phap thuat", 28),

    # Martial Arts (29)
    ("vo hiep", 29),
    ("tien hiep", 29),
    ("tu tien", 29),
    ("kiem hiep", 29),
    ("vo dao", 29),

    # Military (32)
    ("quan su", 32),

    # Mystery (34)
    ("huyen nghi", 34),
    ("trinh tham", 34),
    ("bi an", 34),

    # Parody (38)
    ("dong nhan", 38),
    ("fan fiction", 38),

    # Psychological (39)
    ("tam ly", 39),
    ("tri dau", 39),

    # Romance (41)
    ("ngon tinh", 41),
    ("tinh yeu", 41),
    ("tinh cam", 41),
    ("hon nhan", 41),
    ("ngot sung", 41),

    # School Life (42)
    ("hoc duong", 42),
    ("vuon truong", 42),

    # Science Fiction (43)
    ("khoa huyen", 43),
    ("khoa hoc vien tuong", 43),
    ("tuong lai", 43),

    # Slice of Life (49)
    ("do thi", 49),
    ("sinh hoat", 49),
    ("cuoc song", 49),
    ("nhe nhang", 49),

    # Slow Life (50)
    ("nhan ha", 50),
    ("lam ruong", 50),

    # Sports (51)
    ("the thao", 51),
    ("bong da", 51),

    # Super Power (52)
    ("di nang", 52),
    ("sieu nang luc", 52),
    ("tien hoa", 52),

    # Supernatural (53)
    ("than bi", 53),
    ("linh khi khoi phuc", 53),
    ("he thong", 53),

    # Tragedy (55)
    ("bi kich", 55),

    # Wars (56)
    ("chien tranh", 56),

    # Yuri (59)
    ("bach hop", 59),
    ("yuri", 59),
]


def _remove_diacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt để match keyword."""
    import unicodedata
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text.lower().strip())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def map_tags(tag_list: list[str]) -> list[int]:
    """
    Chuyển list thể loại MTC → list category_id backend.
    Mặc định luôn bao gồm CHINESE_NOVEL_ID (10).
    """
    result = {CHINESE_NOVEL_ID}
    for tag in tag_list:
        tag_clean = _remove_diacritics(tag)
        for keyword, cat_id in _KEYWORD_MAP:
            if _remove_diacritics(keyword) in tag_clean:
                result.add(cat_id)
                break
    return sorted(list(result))


if __name__ == "__main__":
    test = ["Huyền Huyễn", "Tu Tiên", "Hệ Thống", "Ngôn Tình"]
    print("Tags:", test)
    print("Category IDs:", map_tags(test))
