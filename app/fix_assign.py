# -*- coding: utf-8 -*-
"""修复被 delete_one_min.py 误伤的赋值号：把 window.X [ ... ]; 修正为 window.X = [ ... ];
保留当前已过滤的数据，仅补回 '='。
"""
import os, re, json

WS = "G:/gpt/星橙故事铺腾讯/app"
TARGETS = {
    "data": ("js/stories_data.js", "STORY_LIBRARY_EXT"),
    "user": ("js/stories_user.js", "STORY_LIBRARY_USER"),
}

for key, (rel, name) in TARGETS.items():
    path = os.path.join(WS, rel)
    t = open(path, encoding="utf-8").read()
    # 提取数组（兼容有无 '='）
    m = re.search(r"\[.*\]\s*;", t, re.S)
    if not m:
        print(f"[skip] {rel} 未找到数组"); continue
    arr = json.loads(m.group(0).rstrip(";").strip())
    # 检测当前是否已有赋值号
    has_eq = bool(re.search(r"window\." + re.escape(name) + r"\s*=\s*\[", t))
    with open(path, "w", encoding="utf-8") as f:
        f.write("window." + name + " = ")
        f.write(json.dumps(arr, ensure_ascii=False, indent=0))
        f.write(";\n")
    print(f"{key}: 修正赋值号(has_eq={has_eq}) -> {name} 共 {len(arr)} 篇 -> {rel}")
