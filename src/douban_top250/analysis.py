"""Data validation and feature engineering for movie records."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"title", "year", "rating"}
AREA_KEYWORDS = (
    ("中国大陆", "中国大陆"),
    ("中国香港", "中国香港"),
    ("香港", "中国香港"),
    ("中国台湾", "中国台湾"),
    ("台湾", "中国台湾"),
    ("美国", "美国"),
    ("日本", "日本"),
    ("韩国", "韩国"),
    ("英国", "英国"),
    ("法国", "法国"),
    ("印度", "印度"),
    ("意大利", "意大利"),
)
GENRE_KEYWORDS = ("剧情", "喜剧", "动画", "科幻", "犯罪", "爱情", "悬疑", "冒险", "战争", "音乐")


def classify_area(value: object) -> str:
    text = str(value or "")
    for keyword, label in AREA_KEYWORDS:
        if keyword in text:
            return label
    return "其他"


def classify_genre(value: object) -> str:
    text = str(value or "")
    for genre in GENRE_KEYWORDS:
        if genre in text:
            return genre
    return "其他"


def load_movies(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")

    frame = frame.copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["rating"] = pd.to_numeric(frame["rating"], errors="coerce")
    if "votes" in frame:
        frame["votes"] = pd.to_numeric(frame["votes"], errors="coerce").fillna(0).astype(int)
    frame = frame.dropna(subset=["title", "year", "rating"])
    frame = frame[(frame["year"].between(1888, 2100)) & (frame["rating"].between(0, 10))]
    frame["year"] = frame["year"].astype(int)
    frame = frame.drop_duplicates(subset=["title", "year"]).reset_index(drop=True)
    if frame.empty:
        raise ValueError("no valid movie rows remain after cleaning")
    return frame


def enrich_movies(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    region_source = enriched.get("regions", pd.Series("", index=enriched.index))
    genre_source = enriched.get("genres", pd.Series("", index=enriched.index))
    enriched["area"] = region_source.map(classify_area)
    enriched["main_genre"] = genre_source.map(classify_genre)
    enriched["decade"] = (enriched["year"] // 10 * 10).astype(int)
    return enriched


def build_summary(frame: pd.DataFrame) -> dict[str, float | int]:
    return {
        "movie_count": int(len(frame)),
        "average_rating": round(float(frame["rating"].mean()), 2),
        "median_rating": round(float(frame["rating"].median()), 2),
        "earliest_year": int(frame["year"].min()),
        "latest_year": int(frame["year"].max()),
    }

