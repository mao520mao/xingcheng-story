# -*- coding: utf-8 -*-
"""读 baihua_map.jsonl，把维基百科白话正文写回 cn/history jsonl（替换文言文 content）。
保留原典出处：source = 原出处 + "；白话据维基百科《词条》"。
"""
import os, json

WS = "G:/gpt/星橙故事铺腾讯/app"
MAP = os.path.join(WS, "baihua_map.jsonl")
TARGETS = {
    "cn": os.path.join(WS, "cn_stories.jsonl"),
    "history": os.path.join(WS, "history_stories.jsonl"),
}

# 载入 map
m = {}
for line in open(MAP, encoding="utf-8"):
    line = line.strip()
    if not line: continue
    o = json.loads(line)
    m[(o["file"], o["title"])] = o

for fk, path in TARGETS.items():
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    n_rep = 0
    for r in rows:
        key = (fk, r["title"])
        if key in m and m[key]["status"] == "ok" and m[key]["baihua"]:
            orig = r.get("source", "")
            bsrc = m[key]["baihua_src"]
            r["content"] = m[key]["baihua"]
            r["summary"] = m[key]["baihua"][:60]
            # 合并出处：原典 + 白话来源
            if bsrc and bsrc not in orig:
                r["source"] = orig + f"；白话据维基百科《{bsrc}》"
            r["baihua_replaced"] = True
            n_rep += 1
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{fk}: 替换 {n_rep} 篇文言文为白话；总 {len(rows)} 篇 -> {path}")
