"""Generate a responsive ECharts dashboard from a cleaned movie CSV."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import pandas as pd

from .analysis import build_summary, enrich_movies, load_movies


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _series(frame: pd.DataFrame) -> dict[str, object]:
    rating_counts = frame["rating"].round(1).value_counts().sort_index()
    year_counts = frame["year"].value_counts().sort_index()
    area_counts = frame["area"].value_counts().head(10)
    genre_counts = frame["main_genre"].value_counts()
    decade_rating = frame.groupby("decade")["rating"].mean().round(2)
    return {
        "ratingLabels": [str(value) for value in rating_counts.index],
        "ratingValues": rating_counts.astype(int).tolist(),
        "yearLabels": [str(value) for value in year_counts.index],
        "yearValues": year_counts.astype(int).tolist(),
        "areas": [{"name": key, "value": int(value)} for key, value in area_counts.items()],
        "genres": [{"name": key, "value": int(value)} for key, value in genre_counts.items()],
        "decadeLabels": [f"{value}s" for value in decade_rating.index],
        "decadeValues": decade_rating.tolist(),
        "scatter": frame[["year", "rating"]].sort_values("year").values.tolist(),
    }


def build_dashboard(frame: pd.DataFrame, output: str | Path) -> Path:
    frame = enrich_movies(frame)
    summary = build_summary(frame)
    data = _series(frame)
    top_movies = frame.sort_values(["rating", "year"], ascending=[False, False]).head(10)
    table_rows = "".join(
        f"<tr><td>{html.escape(str(row.title))}</td><td>{int(row.year)}</td><td>{float(row.rating):.1f}</td></tr>"
        for row in top_movies.itertuples()
    )
    document = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>豆瓣电影 Top250 数据分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
:root{{--bg:#07111f;--card:#101f34;--line:#1c3554;--text:#e9f1ff;--muted:#91a8c5;--cyan:#36d1dc;--violet:#8b5cf6}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top,#102c4c,var(--bg) 45%);color:var(--text);font-family:Inter,"Microsoft YaHei",sans-serif}}
header{{padding:52px 6vw 22px}} h1{{margin:0;font-size:clamp(30px,5vw,58px)}} header p{{color:var(--muted);max-width:760px;line-height:1.8}}
.stats,.grid{{display:grid;gap:18px;padding:18px 6vw}} .stats{{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}} .grid{{grid-template-columns:repeat(2,minmax(0,1fr));padding-bottom:60px}}
.card{{background:linear-gradient(145deg,rgba(16,31,52,.96),rgba(9,21,38,.96));border:1px solid var(--line);border-radius:18px;box-shadow:0 18px 50px #0005}}
.stat{{padding:22px}} .stat strong{{display:block;font-size:30px;color:var(--cyan)}} .stat span{{color:var(--muted)}} .chart{{height:430px}} .wide{{grid-column:1/-1}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:13px 18px;border-bottom:1px solid var(--line);text-align:left}} th{{color:var(--cyan)}}
@media(max-width:820px){{.grid{{grid-template-columns:1fr}}.wide{{grid-column:auto}}}}
</style></head><body>
<header><h1>电影 Top250<br>数据洞察</h1><p>从榜单数据中观察评分分布、年代变化、地区与题材结构。数据为生成时快照，仅用于学习研究。</p></header>
<section class="stats">
<div class="card stat"><strong>{summary['movie_count']}</strong><span>有效影片</span></div>
<div class="card stat"><strong>{summary['average_rating']}</strong><span>平均评分</span></div>
<div class="card stat"><strong>{summary['median_rating']}</strong><span>评分中位数</span></div>
<div class="card stat"><strong>{summary['earliest_year']}–{summary['latest_year']}</strong><span>年份跨度</span></div>
</section>
<main class="grid"><div id="rating" class="card chart"></div><div id="year" class="card chart"></div><div id="area" class="card chart"></div><div id="genre" class="card chart"></div><div id="decade" class="card chart"></div><div id="scatter" class="card chart"></div>
<div class="card wide"><table><thead><tr><th>高评分影片</th><th>年份</th><th>评分</th></tr></thead><tbody>{table_rows}</tbody></table></div></main>
<script>
const D={_json(data)}; const text='#e9f1ff', grid='#24425f';
function chart(id,opt){{const c=echarts.init(document.getElementById(id),'dark');c.setOption({{backgroundColor:'transparent',textStyle:{{color:text}},...opt}});return c}}
const charts=[
chart('rating',{{title:{{text:'评分分布'}},tooltip:{{trigger:'axis'}},xAxis:{{type:'category',data:D.ratingLabels}},yAxis:{{type:'value',splitLine:{{lineStyle:{{color:grid}}}}}},series:[{{type:'bar',data:D.ratingValues,itemStyle:{{color:'#36d1dc',borderRadius:[6,6,0,0]}}}}]}}),
chart('year',{{title:{{text:'上榜影片年份趋势'}},tooltip:{{trigger:'axis'}},xAxis:{{type:'category',data:D.yearLabels}},yAxis:{{type:'value',splitLine:{{lineStyle:{{color:grid}}}}}},dataZoom:[{{type:'inside'}},{{type:'slider'}}],series:[{{type:'line',smooth:true,data:D.yearValues,lineStyle:{{color:'#8b5cf6'}},areaStyle:{{color:'#8b5cf633'}}}}]}}),
chart('area',{{title:{{text:'地区分布'}},tooltip:{{trigger:'item'}},series:[{{type:'pie',radius:['38%','72%'],data:D.areas}}]}}),
chart('genre',{{title:{{text:'主要类型'}},tooltip:{{trigger:'item'}},series:[{{type:'pie',roseType:'radius',radius:['16%','72%'],data:D.genres}}]}}),
chart('decade',{{title:{{text:'各年代平均评分'}},tooltip:{{trigger:'axis'}},xAxis:{{type:'category',data:D.decadeLabels}},yAxis:{{type:'value',min:'dataMin',splitLine:{{lineStyle:{{color:grid}}}}}},series:[{{type:'line',smooth:true,data:D.decadeValues,itemStyle:{{color:'#ffb86c'}}}}]}}),
chart('scatter',{{title:{{text:'年份与评分关系'}},tooltip:{{trigger:'item'}},xAxis:{{type:'value',name:'年份',splitLine:{{lineStyle:{{color:grid}}}}}},yAxis:{{type:'value',name:'评分',splitLine:{{lineStyle:{{color:grid}}}}}},series:[{{type:'scatter',data:D.scatter,symbolSize:9,itemStyle:{{color:'#36d1dc99'}}}}]}})
]; window.addEventListener('resize',()=>charts.forEach(c=>c.resize()));
</script></body></html>"""
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="从电影 CSV 生成交互式分析仪表盘")
    parser.add_argument("--input", default="data/douban_top250.csv")
    parser.add_argument("--output", default="output/dashboard.html")
    args = parser.parse_args()
    frame = load_movies(args.input)
    output = build_dashboard(frame, args.output)
    print(f"仪表盘已生成：{output}")


if __name__ == "__main__":
    main()

