"""Polite, testable scraper for the public Douban Movie Top250 pages."""

from __future__ import annotations

import argparse
import csv
import random
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://movie.douban.com/top250"
PAGE_SIZE = 25
MAX_ITEMS = 250
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
}


@dataclass(frozen=True)
class Movie:
    rank: int
    title: str
    year: int | None
    rating: float
    votes: int
    director: str
    actors: str
    regions: str
    genres: str
    quote: str
    detail_url: str


def _compact(text: str) -> str:
    return " ".join(text.split())


def parse_metadata(text: str) -> tuple[int | None, str, str, str, str]:
    """Return year, director, actors, regions and genres from an info block."""
    lines = [_compact(line) for line in text.splitlines() if line.strip()]
    people = lines[0] if lines else ""
    facts = lines[1] if len(lines) > 1 else ""

    director_match = re.search(r"导演:\s*(.*?)(?=\s+主演:|$)", people)
    actors_match = re.search(r"主演:\s*(.*)$", people)
    director = director_match.group(1).strip() if director_match else ""
    actors = actors_match.group(1).strip() if actors_match else ""

    parts = [part.strip() for part in facts.split("/") if part.strip()]
    year_match = re.search(r"(?:18|19|20)\d{2}", parts[0] if parts else facts)
    year = int(year_match.group()) if year_match else None
    regions = parts[-2] if len(parts) >= 3 else ""
    genres = parts[-1] if len(parts) >= 2 else ""
    return year, director, actors, regions, genres


def parse_page(html: str) -> list[Movie]:
    """Parse one Top250 page without performing network I/O."""
    soup = BeautifulSoup(html, "html.parser")
    movies: list[Movie] = []
    for item in soup.select("ol.grid_view div.item"):
        rank_node = item.select_one("div.pic em")
        title_node = item.select_one("div.hd span.title")
        rating_node = item.select_one("span.rating_num")
        info_node = item.select_one("div.bd p")
        if not all((rank_node, title_node, rating_node, info_node)):
            continue

        year, director, actors, regions, genres = parse_metadata(info_node.get_text("\n"))
        votes_text = item.select_one("div.star span:last-child")
        votes_match = re.search(r"([\d,]+)\s*人评价", votes_text.get_text() if votes_text else "")
        quote_node = item.select_one("span.inq")
        link_node = item.select_one("div.hd a")

        movies.append(
            Movie(
                rank=int(rank_node.get_text(strip=True)),
                title=title_node.get_text(strip=True),
                year=year,
                rating=float(rating_node.get_text(strip=True)),
                votes=int(votes_match.group(1).replace(",", "")) if votes_match else 0,
                director=director,
                actors=actors,
                regions=regions,
                genres=genres,
                quote=quote_node.get_text(strip=True) if quote_node else "",
                detail_url=link_node.get("href", "") if link_node else "",
            )
        )
    return movies


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(DEFAULT_HEADERS)
    return session


def crawl_top250(
    limit: int = MAX_ITEMS,
    min_delay: float = 2.0,
    max_delay: float = 3.5,
    session: requests.Session | None = None,
) -> list[Movie]:
    if not 1 <= limit <= MAX_ITEMS:
        raise ValueError(f"limit must be between 1 and {MAX_ITEMS}")
    if min_delay < 0 or max_delay < min_delay:
        raise ValueError("delay range is invalid")

    client = session or build_session()
    collected: list[Movie] = []
    seen: set[str] = set()

    for start in range(0, limit, PAGE_SIZE):
        response = client.get(BASE_URL, params={"start": start, "filter": ""}, timeout=15)
        response.raise_for_status()
        page_movies = parse_page(response.text)
        if not page_movies:
            break

        for movie in page_movies:
            identity = movie.detail_url or f"{movie.title}-{movie.year}"
            if identity not in seen:
                seen.add(identity)
                collected.append(movie)
            if len(collected) >= limit:
                return collected

        if start + PAGE_SIZE < limit:
            time.sleep(random.uniform(min_delay, max_delay))
    return collected


def write_csv(movies: Iterable[Movie], output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(movie) for movie in movies]
    if not rows:
        raise ValueError("no movies were collected")
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="低频抓取豆瓣电影 Top250 公开榜单")
    parser.add_argument("--output", default="data/douban_top250.csv")
    parser.add_argument("--limit", type=int, default=250)
    parser.add_argument("--min-delay", type=float, default=2.0)
    parser.add_argument("--max-delay", type=float, default=3.5)
    args = parser.parse_args()

    print("请确认本次访问符合目标网站的服务条款与 robots 规则。")
    movies = crawl_top250(args.limit, args.min_delay, args.max_delay)
    path = write_csv(movies, args.output)
    print(f"已保存 {len(movies)} 条去重记录：{path}")


if __name__ == "__main__":
    main()

