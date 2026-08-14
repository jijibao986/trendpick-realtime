# 印选 TrendPick v2 数据 Schema

> 版本：v2 | 日期：2026-08-10 | 基于 TrendTee 优势吸收改造

## 单条事件记录（window.EVENTS 元素）

### 保留字段（v1 兼容）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | UUID，唯一标识 |
| country | string | "th" \| "my" |
| cat | string | 英文分类键（celebrity/concert_show/film_tv/gaming/meme/other/society/sports/politics/ecommerce/platform_search） |
| catCn | string | 中文分类名 |
| stars | number | 印花指数 1-4 |
| printType | string | "文字款" \| "图案款" \| "文字+图案" |
| risk | string | "高/中风险" \| "低风险" |
| hotDays | number | 还热 N 天 |
| titleCn | string | 中文标题 |
| titleOrig | string | 原文标题（含外语括号中文翻译） |
| summary | string | 摘要 |
| tags | string[] | 标签数组 |
| sensitive | bool | 红线标记 |

### 改造字段（v2 升级）
| 字段 | 类型 | 说明 |
|------|------|------|
| **sources** | object[] | **结构化来源列表**（替换原逗号字符串） |
| credibilityScore | number | 可信度分 0-100（sources 加权平均） |
| buzzIndex | number | 讨论热度 0-100 |
| **timeline** | object[] | **多节点事件脉络**（新增） |
| timeAbs | string | 首发时间（保留，用于排序） |
| timeRel | string | 相对时间描述 |
| timezoneNote | string | 时区备注（如 "UTC+8"） |
| **media** | object[] | **真实配图列表**（新增） |
| cover | string | 卡片封面图路径（= media[0].thumb） |
| hasMedia | bool | 是否有真实配图 |
| imageSource | string | 图源署名（如 "图源：Netflix / Google Trends"） |
| **primaryUrl** | string | **原始报道主链接**（新增） |
| sourceBreadth | object | 来源覆盖广度 { local, global, social_only } |

### sources[] 结构
```js
{
  name: string,        // 来源名称（如 "Google Trends"、"Khaosod"、"Billboard TH"）
  type: string,        // "trends" | "news" | "social" | "official" | "chart" | "streaming" | "forum"
  url: string,         // 来源链接（可为空）
  credibility: string, // "高" | "中" | "低"
  region: string,      // "th" | "my" | "global"
  mention: number      // 提及量/排名/播放量等原始数值
}
```

### timeline[] 结构
```js
{
  ts: string,       // ISO 时间戳（如 "2026-08-09T15:20:00Z"）
  label: string,    // 节点描述（如 "Netflix 上线新剧"、"外媒开始报道"）
  type: string,     // "release" | "report" | "trend" | "event" | "social"
  sourceRef: string // 对应 sources 索引或 URL（可选）
}
```

### media[] 结构
```js
{
  type: string,     // "poster" | "screenshot" | "trends" | "news"
  url: string,      // 完整 URL 或本地路径
  thumb: string,    // 缩略图路径（本地相对路径 img/real/...）
  caption: string,  // 图片说明
  source: string     // 图源署名（如 "Netflix"、"Google Trends"、"Major Cineplex"）
}
```

## 向后兼容
- v1 字段全部保留，新增字段均为可选
- app.js 渲染时对 v2 新字段做 fallback：
  - `sources` 若为字符串 → 显示为旧式文本
  - `media` 为空或不存在 → 显示渐变占位
  - `timeline` 为空 → 不渲染脉络区块
  - `primaryUrl` 为空 → 不显示跳转按钮
