# 豆瓣电影 Top250 数据分析与交互式可视化

一个面向课程设计与数据分析作品集的 Python 项目：以豆瓣电影 Top250 页面为数据源，完成网页解析、数据清洗、统计分析和 ECharts 交互式仪表盘生成。

> 本项目仅用于学习和研究。请遵守目标网站的服务条款与 robots 规则，控制请求频率；仓库不分发完整抓取数据。

## 在线成果

- [打开交互式可视化快照](docs/index.html)

该 HTML 是课程项目生成的历史快照，依赖 ECharts CDN。GitHub 文件预览不会执行 JavaScript，下载后用浏览器打开即可查看。

## 项目亮点

- 将原先互相重复的四个脚本重构为职责清晰的抓取、分析和可视化模块。
- 修正“Top250”被误写成“Top500”的数据口径问题，抓取上限强制为 250。
- 移除源码中的 MySQL 明文密码，默认使用可移植的 CSV 工作流。
- 抓取过程提供超时、自动重试、随机限速、去重和提前终止机制。
- 解析逻辑和数据清洗逻辑均有自动化测试，不依赖网络即可验证。
- 仪表盘包含评分分布、年份趋势、地区分布、类型分布、年代评分和年份—评分关系。

## 目录结构

```text
keshe/
├── src/douban_top250/
│   ├── scraper.py       # 请求、页面解析与 CSV 导出
│   ├── analysis.py      # 数据校验、清洗与特征提取
│   └── dashboard.py     # 生成 ECharts 交互式仪表盘
├── tests/               # 离线单元测试与 HTML fixture
├── data/
│   └── sample_movies.csv
├── docs/
│   └── index.html       # 历史可视化成果
├── pyproject.toml
└── requirements.txt
```

## 快速开始

建议使用 Python 3.9 或更高版本：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
```

先用仓库内的小型示例数据生成仪表盘：

```bash
python -m douban_top250.dashboard \
  --input data/sample_movies.csv \
  --output output/dashboard.html
```

如确认符合目标网站的访问政策，可低频抓取公开榜单：

```bash
python -m douban_top250.scraper \
  --output data/douban_top250.csv \
  --limit 250 \
  --min-delay 2.0 \
  --max-delay 3.5
```

然后生成完整仪表盘：

```bash
python -m douban_top250.dashboard \
  --input data/douban_top250.csv \
  --output output/dashboard.html
```

也可以安装为命令行工具：

```bash
python -m pip install -e .
douban-scrape --help
douban-dashboard --help
```

## 测试

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

测试使用本地 HTML fixture，不会访问豆瓣。

## 数据字段

| 字段 | 含义 |
| --- | --- |
| `rank` | 榜单名次 |
| `title` | 电影名称 |
| `year` | 上映年份 |
| `rating` | 页面展示评分 |
| `votes` | 页面展示评价人数 |
| `director` / `actors` | 主创信息 |
| `regions` / `genres` | 地区与类型文本 |
| `quote` | 页面展示短评 |
| `detail_url` | 详情页链接 |

## 局限性

- 榜单和评分会随时间变化，历史快照不代表当前结果。
- 页面结构调整可能导致解析规则失效，需要更新 fixture 和选择器。
- 地区与类型分类采用关键词规则，适合课程分析，不等同于专业电影数据库标注。
- 本项目不绕过登录、验证码或反爬限制；遇到限制时应停止请求。

