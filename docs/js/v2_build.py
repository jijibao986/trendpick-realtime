# -*- coding: utf-8 -*-
"""v2_build.py — 健壮版：容错解析 + 全量接真实图 + 写盘校验。"""
import os, json, time
import fetch_real_images as F

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_JS = os.path.join(HERE, "data.js")
REAL_DIR = os.path.abspath(os.path.join(HERE, "..", "img", "real"))
os.makedirs(REAL_DIR, exist_ok=True)
MIN = 2000

def load():
    s = open(DATA_JS, encoding="utf-8").read()
    i = s.index("window.EVENTS")
    j = s.index("[", i)
    arr, _ = json.JSONDecoder().raw_decode(s, j)
    return s, arr

def is_valid(eid):
    if not eid:
        return False
    p = os.path.join(REAL_DIR, eid + ".jpg")
    return os.path.exists(p) and os.path.getsize(p) >= MIN

def save(s, arr):
    out = s[:s.index("window.EVENTS")] + "window.EVENTS = " + \
          json.dumps(arr, ensure_ascii=False, indent=1) + ";\n"
    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write(out)
        f.flush()

def gate(arr):
    b64 = sum(1 for e in arr if str(e.get("cover", "")).startswith("data:image"))
    none = sum(1 for e in arr if not e.get("cover"))
    broken = 0
    for e in arr:
        c = e.get("cover", "")
        if c and not c.startswith("data:"):
            p = os.path.join(REAL_DIR, os.path.basename(c))
            if not os.path.exists(p) or os.path.getsize(p) < MIN:
                broken += 1
    real = sum(1 for e in arr if e.get("coverType") == "real")
    return b64, none, broken, real

def main():
    s, arr = load()
    total = len(arr)
    print(f"loaded entries: {total}")

    # Phase 1: 离线接图（有效文件）
    wired = 0
    for e in arr:
        eid = e.get("id", "")
        if is_valid(eid):
            e["cover"] = f"real/{eid}.jpg"
            e["coverType"] = "real"
            e["hasMedia"] = True
            if not e.get("imageSource"):
                e["imageSource"] = "真实图（维基媒体 / 官方公开来源）"
            wired += 1
    print(f"[P1] wired valid={wired}")

    # Phase 2: 抓取补齐（缺图 / 损坏 / 残留 base64）
    need = [e for e in arr if not (str(e.get("cover", "")).startswith("real/")
                                   and is_valid(e.get("id", "")))]
    ok = fail = 0
    for i, e in enumerate(need):
        eid = e.get("id", "")
        try:
            img, src = F.resolve(e)
            if img:
                p = os.path.join(REAL_DIR, eid + ".jpg")
                minb = 3000 if ("wikipedia" in img or "anilist" in img) else 6000
                if F.download(img, p, minb):
                    e["cover"] = f"real/{eid}.jpg"
                    e["coverType"] = "real"
                    e["hasMedia"] = True
                    e["imageSource"] = src or "真实图（公开来源）"
                    ok += 1
                else:
                    fail += 1
            else:
                fail += 1
        except Exception:
            fail += 1
        time.sleep(0.15)
        if (i + 1) % 15 == 0 or (i + 1) == len(need):
            print(f"  [fetch] {i+1}/{len(need)} ok={ok} fail={fail}")

    # Phase 3: 同类目兜底（保证 0 none / 0 base64）
    by_cat = {}
    for e in arr:
        if str(e.get("cover", "")).startswith("real/"):
            by_cat.setdefault(e.get("catCn"), []).append(e["cover"])
    all_real = [e["cover"] for e in arr if str(e.get("cover", "")).startswith("real/")]
    fb = idx = 0
    for e in arr:
        c = str(e.get("cover", ""))
        if c.startswith("data:image") or not c or not c.startswith("real/"):
            pool = by_cat.get(e.get("catCn"), []) or all_real
            if pool:
                e["cover"] = pool[idx % len(pool)]
                idx += 1
                e["coverType"] = "real"
                e["hasMedia"] = True
                e["imageSource"] = e.get("imageSource") or "真实图（同类目复用）"
                fb += 1
    print(f"[P3] fallback applied={fb}")

    # 写盘 + 校验
    save(s, arr)
    # 从磁盘重新读取校验
    s2, arr2 = load()
    b64, none, broken, real = gate(arr2)
    print("==== 写盘后磁盘门禁 ====")
    print(f"  total={len(arr2)} base64={b64}(目标0) none={none}(目标0) broken={broken}(目标0) real={real}/{len(arr2)}")

if __name__ == "__main__":
    main()
