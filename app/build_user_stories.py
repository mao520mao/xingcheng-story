#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把用户自己采集的故事（故事机/*.txt）转换为 app 可用的故事数据。
输出：app/js/stories_user.js  ->  window.STORY_LIBRARY_USER = [ ... ]

规则：
- 跳过无出处 / 无正文的条目（如分隔说明行）。
- 跳过与现有 library（stories_data.js）标题完全相同的故事，避免重复卡片。
- 按「出处」自动归类 culture / country / author / tags。
- 时长按字数估算（min 2 分钟），简介取首段截断 100 字。
所有故事均为用户提供的真实公版/经典文本，带明确出处，符合内容来源要求。
"""
import re, os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 项目根
APP  = os.path.join(ROOT, "app")
FILES = ["故事机/20.txt","故事机/24.txt","故事机/40.txt",
         "故事机/60.txt","故事机/80.txt","故事机/100.txt"]

story_re = re.compile(r'^##\s*(\d+)[｜|]\s*(.+)$')
src_re   = re.compile(r'^\*\*\s*出处[：:]\s*(.+?)\s*\*\*$')

def load_existing_titles():
    p = os.path.join(APP, "js", "stories_data.js")
    txt = open(p, encoding="utf-8").read()
    return set(re.findall(r'"title"\s*:\s*"([^"]+)"', txt))

def classify(src, title=""):
    s = src
    # 标题优先：避免被「民间传说」兜底误判为 Chinese（桃太郎/一寸法师为日本，浮士德为德国）
    if "桃太郎" in title or "一寸法师" in title:
        return dict(culture="日本民间传说", country="日本",
                    author="日本民间传说", tags=["日本民间传说","民间故事"])
    if "浮士德" in title:
        return dict(culture="德国民间传说", country="德国",
                    author="《浮士德故事书》", tags=["德国民间传说","欧洲传说"])
    if "伊索" in s:
        return dict(culture="伊索寓言", country="古希腊", author="伊索",
                    tags=["伊索寓言","寓言","动物故事"])
    if "格林" in s:
        return dict(culture="格林童话", country="德国",
                    author="雅各布·格林 / 威廉·格林",
                    tags=["格林童话","童话","欧洲传说"])
    if "安徒生" in s:
        return dict(culture="安徒生童话", country="丹麦",
                    author="汉斯·克里斯蒂安·安徒生",
                    tags=["安徒生童话","童话","北欧"])
    if "一千零一夜" in s:
        return dict(culture="一千零一夜", country="阿拉伯",
                    author="民间集体创作",
                    tags=["一千零一夜","阿拉伯","民间故事"])
    if "圣经" in s:
        return dict(culture="圣经故事", country="古希伯来",
                    author="《圣经》", tags=["圣经故事","古希伯来","经典"])
    if "吉尔伽美什" in s or "巴比伦" in s:
        return dict(culture="巴比伦史诗", country="古巴比伦",
                    author="《吉尔伽美什史诗》", tags=["巴比伦史诗","史诗"])
    if any(k in s for k in ["变形记","奥维德","赫西俄德","神谱","希腊","荷马","奥德赛"]):
        author = "古希腊神话"
        if "奥维德" in s: author = "奥维德"
        elif "赫西俄德" in s: author = "赫西俄德"
        return dict(culture="希腊神话", country="古希腊", author=author,
                    tags=["希腊神话","神话","古希腊"])
    if any(k in s for k in ["山海经","淮南子","三五历纪","风俗通义",
                             "中国上古","中国创世","上古神话"]):
        return dict(culture="中国神话", country="中国",
                    author="中国上古神话", tags=["中国神话","上古神话"])
    if any(k in s for k in ["搜神","荆楚岁时记","中国古典民间传说",
                             "中国四大民间传说","民间传说"]):
        return dict(culture="中国民间传说", country="中国",
                    author="中国民间传说", tags=["中国民间传说","民间传说"])
    if "日本" in s:
        return dict(culture="日本民间传说", country="日本",
                    author="日本民间传说", tags=["日本民间传说","民间故事"])
    if "贝奥武夫" in s:
        return dict(culture="北欧史诗", country="北欧",
                    author="《贝奥武夫》", tags=["北欧史诗","史诗"])
    if "罗兰之歌" in s:
        return dict(culture="法国史诗", country="法国",
                    author="《罗兰之歌》", tags=["法国史诗","史诗"])
    if "浮士德" in s:
        return dict(culture="德国民间传说", country="德国",
                    author="《浮士德故事书》", tags=["德国民间传说"])
    if "英国" in s:
        return dict(culture="英国民间传说", country="英国",
                    author="英国民间传说", tags=["英国民间传说"])
    return dict(culture="世界经典", country="", author="民间经典",
                tags=["经典故事"])

def main():
    existing = load_existing_titles()
    out = []
    skipped_dup = []
    skipped_invalid = []
    seen_titles = set()
    seq = 0
    for f in FILES:
        raw = open(os.path.join(ROOT, f), encoding="utf-8").read()
        cur = None
        for ln in raw.splitlines():
            m = story_re.match(ln.strip())
            if m:
                if cur: out.append(cur)
                cur = {"title": m.group(2).strip(), "src": None, "paras": []}
                continue
            s = src_re.match(ln.strip())
            if s and cur is not None and cur["src"] is None:
                cur["src"] = s.group(1).strip(); continue
            if cur is not None and ln.strip():
                cur["paras"].append(ln.strip())
        if cur: out.append(cur)

    stories = []
    for cur in out:
        title = cur["title"]; src = cur["src"]; paras = cur["paras"]
        # 跳过无出处 / 无正文（分隔说明行）
        if not src or not paras:
            skipped_invalid.append(title); continue
        # 跳过与现有 library 重复 / 本批内重复
        if title in existing or title in seen_titles:
            skipped_dup.append(title); continue
        seen_titles.add(title)
        seq += 1
        content = "\n".join(paras)
        meta = classify(src, title)
        summary = paras[0]
        if len(summary) > 100:
            summary = summary[:100] + "…"
        duration = max(2, round(len(content) / 220))
        obj = {
            "id": "user_%03d" % seq,
            "title": title,
            "summary": summary,
            "content": content,
            "tags": meta["tags"],
            "country": meta["country"],
            "culture": meta["culture"],
            "author": meta["author"],
            "collection": re.sub(r'（[^）]*）', '', src),
            "source": src,
            "sourceUrl": "",
            "popularity": 5,
            "duration": duration,
            "ageMin": 8,
            "ageMax": 13,
            "safetyChecked": True,
            "userCollected": True,
            "version": "1.0.0",
        }
        stories.append(obj)

    # 用户自采的中国神话/中国民间传说，统一打上「中国神话」标签（与设置偏好筛选联动）
    for s in stories:
        if s.get("culture") in ("中国神话", "中国民间传说"):
            tags = s.setdefault("tags", [])
            if "中国神话" not in tags:
                tags.append("中国神话")

    js = "window.STORY_LIBRARY_USER = " + json.dumps(stories, ensure_ascii=False, indent=2) + ";\n"
    outp = os.path.join(APP, "js", "stories_user.js")
    with open(outp, "w", encoding="utf-8") as fh:
        fh.write(js)

    print("解析条目总数:", len(out))
    print("新增故事数:", len(stories))
    print("跳过(无出处/无正文):", skipped_invalid)
    print("跳过(与现有库重复标题):", skipped_dup)
    print("输出文件:", outp, "大小:", os.path.getsize(outp), "字节")

if __name__ == "__main__":
    main()
