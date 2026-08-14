# -*- coding: utf-8 -*-
"""把 data.js 的 cat 字段统一为 SCHEMA_v2 英文枚举键，并补满 primaryUrl。"""
import json, os

DATA_JS = "data.js"
IMG = os.path.abspath("../img/real")

# cat 中文/旧值 -> v2 规范英文枚举键
CAT_MAP = {
    "明星八卦": "celebrity",
    "网络热梗": "meme",
    "影视剧": "film_tv",
    "其他热搜": "other",
    "游戏电竞": "gaming",
    "体育": "sports",
    "社会民生": "society",
    # 规范扩展键（v2 升级计划新增）
    "电商政策": "ecommerce",
    "平台热搜": "platform_search",
}
# 已被规范的英文键（保持不变）
SPEC_OK = {"celebrity","concert_show","film_tv","gaming","meme",
           "other","society","sports","politics","ecommerce","platform_search"}

raw = open(DATA_JS, encoding="utf-8").read()
start = raw.index("[")
arr, _ = json.JSONDecoder().raw_decode(raw, start)

cat_fixed = 0
url_fixed = 0
for e in arr:
    c = e.get("cat")
    if c in CAT_MAP:
        e["cat"] = CAT_MAP[c]
        cat_fixed += 1
    elif c in SPEC_OK:
        pass
    else:
        # 兜底：按 catCn 映射，仍找不到则归 other
        e["cat"] = CAT_MAP.get(e.get("catCn", ""), "other")
        cat_fixed += 1

    # 补 primaryUrl：取 sources 中第一个非空 url（优先 official）
    if not e.get("primaryUrl"):
        srcs = e.get("sources") or []
        cand = None
        for s in srcs:
            if isinstance(s, dict) and s.get("url"):
                if s.get("type") == "official":
                    cand = s["url"]; break
        if cand is None:
            for s in srcs:
                if isinstance(s, dict) and s.get("url"):
                    cand = s["url"]; break
        if cand:
            e["primaryUrl"] = cand
            url_fixed += 1

# 写盘
out = raw[:start] + json.dumps(arr, ensure_ascii=False, indent=1) + ";\n"
with open(DATA_JS, "w", encoding="utf-8") as f:
    f.write(out)

# 磁盘复核
raw2 = open(DATA_JS, encoding="utf-8").read()
arr2, _ = json.JSONDecoder().raw_decode(raw2, raw2.index("["))
from collections import Counter
print("cat 修正条数:", cat_fixed, "| primaryUrl 补满条数:", url_fixed)
print("TOTAL:", len(arr2))
print("cat 取值分布:", dict(Counter(e.get("cat") for e in arr2)))
print("primaryUrl 仍缺失:", sum(1 for e in arr2 if not e.get("primaryUrl")),
      "(应为 0 或仅无来源链接的条目)")
print("各 cat 是否均在规范枚举:", all(e.get("cat") in SPEC_OK for e in arr2))
PY = None
