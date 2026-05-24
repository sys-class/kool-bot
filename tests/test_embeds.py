from services import embeds


def test_ok_color():
    e = embeds.ok("title", "desc")
    assert e.color.value == embeds.ACCENT
    assert e.title == "title"
    assert e.description == "desc"


def test_err_color_and_default_title():
    e = embeds.err("что-то сломалось")
    assert e.color.value == embeds.ERROR
    assert e.title == "ошибка"
    assert e.description == "что-то сломалось"


def test_title_lowercased():
    e = embeds.ok("ВЕРХНИЙ РЕГИСТР")
    assert e.title == "верхний регистр"


def test_no_title_no_description():
    e = embeds.ok()
    assert e.title is None or e.title == ""
    assert e.description is None or e.description == ""


def test_bar_full():
    assert embeds.bar(100, width=10) == embeds.BAR_FILLED * 10


def test_bar_empty():
    assert embeds.bar(0, width=10) == embeds.BAR_EMPTY * 10


def test_bar_half():
    s = embeds.bar(50, width=10)
    assert s.count(embeds.BAR_FILLED) == 5
    assert s.count(embeds.BAR_EMPTY) == 5


def test_bar_width_preserved():
    for rate in (0, 17, 33, 50, 88, 100):
        assert len(embeds.bar(rate, width=12)) == 12
