# -*- coding: utf-8 -*-
"""读 baihua_map_pw.jsonl，把百度百科真实白话正文写回 cn/history jsonl（替换文言文 content）。
非 AI 生成：白话来自百度百科词条真人编写的正文。
保留原典出处：source = 原出处 + "；白话据百度百科《词条》"。
仅当 map 中该条 status==ok 且 baihua 非空时替换。
"""
import os, json

WS = "G:/gpt/星橙故事铺腾讯/app"
MAP = os.path.join(WS, "baihua_map_pw.jsonl")
TARGETS = {
    "cn": os.path.join(WS, "cn_stories.jsonl"),
    "history": os.path.join(WS, "history_stories.jsonl"),
}

if not os.path.exists(MAP):
    print("未找到", MAP, "（先跑 fetch_baihua_pw.py）")
    raise SystemExit(0)

# 载入 map
m = {}
for line in open(MAP, encoding="utf-8"):
    line = line.strip()
    if not line: continue
    o = json.loads(line)
    m[(o["file"], o["title"])] = o

for fk, path in TARGETS.items():
    if not os.path.exists(path):
        print("跳过(文件不存在):", path); continue
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    n_rep = 0
    for r in rows:
        key = (fk, r["title"])
        if key in m and m[key]["status"] == "ok" and m[key]["baihua"]:
            orig = r.get("source", "")
            bsrc = m[key]["baihua_src"]
            r["content"] = m[key]["baihua"]
            r["summary"] = m[key]["baihua"][:60]
            if bsrc and bsrc not in orig:
                r["source"] = orig + f"；白话据百度百科《{bsrc}》"
            r["baihua_replaced"] = True
            n_rep += 1
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{fk}: 替换 {n_rep} 篇文言文为白话；总 {len(rows)} 篇 -> {path}")
