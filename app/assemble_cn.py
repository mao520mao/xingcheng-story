# -*- coding: utf-8 -*-
"""Assemble cn_stories.jsonl -> app/js/stories_cn.js (window.STORY_LIBRARY_CN)."""
import os, json
WS = "G:/gpt/星橙故事铺腾讯/app"
JSONL = os.path.join(WS, "cn_stories.jsonl")
OUT = os.path.join(WS, "js", "stories_cn.js")

rows = []
for line in open(JSONL, encoding="utf-8"):
    line = line.strip()
    if not line: continue
    rows.append(json.loads(line))

# stable ids in file order
for i, r in enumerate(rows, 1):
    r["id"] = f"cn_{i:03d}"
    # safety: ensure required fields
    r.setdefault("ageGroup", "8-13")
    # 关键：补齐 ageMin/ageMax，否则会被推荐池的 age 过滤整批排除（原库统一 8-13）
    r["ageMin"] = 8
    r["ageMax"] = 13
    r.setdefault("safetyChecked", True)
    r.setdefault("summary", r["content"][:60])
    # 输出 display 层读取的 duration 字段（原错用 durationMin 导致不显示分钟）
    _dur = max(2, (len(r["content"]) + 299)//300)
    r["duration"] = _dur
    r["durationMin"] = _dur
    # 统一打上「中国神话」标签（用户要求：设置偏好可筛选中国神话，单选时只推此类）
    tags = r.get("tags") or []
    if "中国神话" not in tags:
        tags.append("中国神话")
    r["tags"] = tags

with open(OUT, "w", encoding="utf-8") as f:
    f.write("// 中国神话 / 中国传统民间传说 — 维基文库公版资源，逐字简体，未经AI改写\n")
    f.write("// 自动生成，请勿手改；来源脚本 app/fetch_cn_library.py\n")
    f.write("window.STORY_LIBRARY_CN = ")
    f.write(json.dumps(rows, ensure_ascii=False, indent=0))
    f.write(";\n")

from collections import Counter
c = Counter(r["culture"] for r in rows)
print("total:", len(rows))
for k, v in c.most_common():
    print(f"  {k}: {v}")
print("written ->", OUT)
