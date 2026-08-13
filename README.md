# 印选 TrendPick v2 — 云端实时榜单（零 Key）

每小时由 GitHub Actions 自动运行 `scrape_realtime.py`，爬取泰/马双市场公开榜单与热搜
（trends24 泰/马热搜、Apple Music 泰/马、Steam 热门游戏、MyAnimeList 动漫），
生成 `realtime.js`（含中文翻译与远程配图 URL），推送到本仓库并由 GitHub Pages 自动托管。

主站点（CloudStudio 上的印选 v2）每 5 分钟动态加载本仓库的 `realtime.js` 并合并展示，
**因此即使本机电脑关机，站点数据也会持续更新**。

## 数据源（全部免费公开，无需任何 API Key / 大模型）
- Twitter/X 热搜：trends24.in（泰国 / 马来西亚）
- 音乐榜单：Apple Music RSS（泰国 / 马来西亚）
- 游戏热度：Steam Charts API
- 动漫热度：MyAnimeList

## 文件
- `scrape_realtime.py` — 纯 Python 标准库爬虫（无第三方依赖）
- `realtime.js` — 生成物（被主站点加载）
- `.github/workflows/update.yml` — 每小时定时任务 + 手动触发

## 备注
- 公开仓库 60 天无活动会暂停定时任务；保持访问或用 Actions 页手动 Run workflow 保活。
- 抓取全失败时会自动"沿用版"兜底（推进时间戳、标 carried_over），绝不静止在旧日期。
