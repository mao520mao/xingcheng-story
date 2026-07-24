# -*- coding: utf-8 -*-
"""删除 reading duration == 1 的所有文章（按用户指令）。
处理 stories_data.js（原库 379）与 stories_user.js（用户库 89）。
解析 global 数组 -> 过滤 duration!=1 -> 重写，保持合法 JS。
"""
import os, re, json

WS = "G:/gpt/星橙故事铺腾讯/app"
TARGETS = {
    "data": os.path.join(WS, "js", "stories_data.js"),
    "user": os.path.join(WS, "js", "stories_user.js"),
}

def load_arr(path):
    t = open(path, encoding="utf-8").read()
    # 兼容有无 '='：抓取全局名与数组
    nm = re.search(r"window\.(\w+)\s*\[", t)
    name = nm.group(1) if nm else "STORY_LIBRARY"
    m = re.search(r"\[.*\]\s*;", t, re.S)
    arr = json.loads(m.group(0).rstrip(";").strip())
    return name, arr

for key, path in TARGETS.items():
    if not os.path.exists(path):
        print(f"[skip] {path} 不存在")
        continue
    name, arr = load_arr(path)
    before = len(arr)
    kept = [s for s in arr if s.get("duration") != 1]
    removed = before - len(kept)
    with open(path, "w", encoding="utf-8") as f:
        f.write("window." + name + " = ")
        f.write(json.dumps(kept, ensure_ascii=False, indent=0))
        f.write(";\n")
    print(f"{key}: {before} -> {len(kept)} （删除 duration==1 共 {removed} 篇）-> {path}")
