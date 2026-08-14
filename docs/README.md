# 印选 TrendPick · 泰马热点选品雷达

仿照 TrendTee（泰国马来西亚热点选品）思路搭建的**自有**印花 T 恤热点聚合站。
纯静态站点（HTML/CSS/JS），无需后端，可直接双击 `index.html` 打开，或托管到任意静态空间。

## 功能
- 🌏 国别切换：泰国 / 马来西亚 / 全部
- 🗂 9 大分类筛选：明星八卦、演唱会综艺、影视剧、游戏电竞、网络热梗、其他热搜、社会民生、体育、政党选举
- ⭐ 按印花指数（★1–4）、风险（高/中/低）、还热天数筛选与排序
- 🔍 关键词搜索（热点名 / 剧名 / 明星 / 标签）
- ▤ 卡片 / 时间线 两种视图
- 💡 点击卡片查看「印花建议」（按印花类型、星级、风险自动生成打样建议）
- 🛡 默认开启「仅看可印」：自动屏蔽王室 / 政治人物 / 宗教符号等敏感类目（可关闭）
- 🎨 AI 概念图灵感库（14 张 T 恤图案概念稿）

## 目录
```
site/
├─ index.html        # 页面结构
├─ css/style.css     # 样式（可改配色变量 --brand 等）
├─ js/data.js        # 数据集（window.EVENTS）
├─ js/app.js         # 交互逻辑
├─ js/build_data.py  # 将 TrendTee 抓取结果转为 data.js
└─ img/              # AI 概念图
```

## 更新数据
1. 抓取 TrendTee 最新事件，保存为 `events.json`（字段：country/cat/cat_cn/url/stars/tags/print_type/cat_label/time_abs/time_rel/hot_days/risk/title_cn/title_orig/summary/source_count/sources）
2. 运行 `python js/build_data.py` → 重新生成 `js/data.js`
3. 刷新页面即可

## 部署
- 本地预览：`python -m http.server 8080` 后访问 `http://127.0.0.1:8080`
- 上线：把整个 `site/` 文件夹上传到 Vercel / Netlify / GitHub Pages / 任意虚拟主机即可

> 数据来自公开热搜聚合，仅供选品参考；风险等级不代表法律意见，敏感类目默认屏蔽，请自行核定授权与合规。
