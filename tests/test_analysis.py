import pandas as pd

from douban_top250.analysis import build_summary, enrich_movies


def test_enrichment_and_summary():
    frame = pd.DataFrame(
        {
            "title": ["A", "B"],
            "year": [1994, 2001],
            "rating": [9.7, 9.5],
            "regions": ["美国", "日本"],
            "genres": ["剧情 犯罪", "动画 奇幻"],
        }
    )
    enriched = enrich_movies(frame)
    assert enriched["area"].tolist() == ["美国", "日本"]
    assert enriched["main_genre"].tolist() == ["剧情", "动画"]
    assert enriched["decade"].tolist() == [1990, 2000]
    assert build_summary(enriched) == {
        "movie_count": 2,
        "average_rating": 9.6,
        "median_rating": 9.6,
        "earliest_year": 1994,
        "latest_year": 2001,
    }

