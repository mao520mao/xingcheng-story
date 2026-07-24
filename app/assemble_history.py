# -*- coding: utf-8 -*-
"""Assemble history_stories.jsonl -> app/js/stories_history.js (window.STORY_LIBRARY_HISTORY)."""
import os, json
WS = "G:/gpt/星橙故事铺腾讯/app"
JSONL = os.path.join(WS, "history_stories.jsonl")
OUT = os.path.join(WS, "js", "stories_history.js")

rows = []
for line in open(JSONL, encoding="utf-8"):
    line = line.strip()
    if not line: continue
    rows.append(json.loads(line))

# stable ids in file order
for i, r in enumerate(rows, 1):
    r["id"] = f"hist_{i:03d}"
    r.setdefault("ageGroup", "8-13")
    r["ageMin"] = 8
    r["ageMax"] = 13
    r.setdefault("safetyChecked", True)
    r.setdefault("summary", r["content"][:60])
    # 输出 display 层读取的 duration 字段（原错用 durationMin 导致不显示分钟）
    _dur = max(2, (len(r["content"]) + 299)//300)
    r["duration"] = _dur
    r["durationMin"] = _dur
    # 统一打上「历史趣事」标签
    tags = r.get("tags") or []
    if "历史趣事" not in tags:
        tags.append("历史趣事")
    r["tags"] = tags

with open(OUT, "w", encoding="utf-8") as f:
    f.write("// 历史趣事 — 维基百科白话正文，逐字简体，未经AI改写；含出处（维基条目+原始史籍）\n")
    f.write("// 自动生成，请勿手改；来源脚本 app/fetch_history.py\n")
    f.write("window.STORY_LIBRARY_HISTORY = ")
    f.write(json.dumps(rows, ensure_ascii=False, indent=0))
    f.write(";\n")

from collections import Counter
c = Counter(r["era"] for r in rows)
print("total:", len(rows))
for k, v in c.most_common():
    print(f"  {k}: {v}")
print("written ->", OUT)
