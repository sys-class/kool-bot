from cogs.uwuify import felinid_accent


def test_letter_replacement_en():
    assert felinid_accent("hello") == "hewwo"


def test_letter_replacement_ru():
    assert felinid_accent("привет") == "пвивет"


def test_case_preserved_in_letters():
    assert felinid_accent("Lol") == "Wow"


def test_word_map_replacement():
    assert "kawaii" in felinid_accent("you are cute")


def test_word_map_case_preserved():
    out = felinid_accent("Cute")
    assert out.startswith("K") and "awaii" in out


def test_urls_preserved():
    url = "https://example.com/path?q=1"
    text = f"check this {url} please"
    out = felinid_accent(text)
    assert url in out


def test_empty_string():
    assert felinid_accent("") == ""


def test_no_match_unchanged():
    assert felinid_accent("xyz 123") == "xyz 123"
