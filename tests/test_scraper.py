from pathlib import Path

import pytest

from douban_top250.scraper import crawl_top250, parse_page


FIXTURE = Path(__file__).parent / "fixtures" / "top250_page.html"


def test_parse_page_extracts_structured_movies():
    movies = parse_page(FIXTURE.read_text(encoding="utf-8"))
    assert len(movies) == 2
    assert movies[0].rank == 1
    assert movies[0].title == "测试电影甲"
    assert movies[0].year == 1994
    assert movies[0].votes == 1_234_567
    assert movies[0].director == "张三"
    assert movies[0].actors == "李四 / 王五"
    assert movies[0].genres == "剧情 犯罪"
    assert movies[1].quote == ""


@pytest.mark.parametrize("limit", [0, 251])
def test_limit_must_match_top250_scope(limit):
    with pytest.raises(ValueError):
        crawl_top250(limit=limit)

