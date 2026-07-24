# -*- coding: utf-8 -*-
"""从两本电子书提取真实童话，生成新的 stories_data.js（覆盖全部旧库）。
- 安徒生童话.epub：按 partNNNN 文件分组，h1 为篇名（排除目录/序言等前言）
- 王尔德童话.mobi：连续文本，按 9 篇已知开头句切分
- 标签：安徒生→["安徒生童话"]，王尔德→["王尔德童话"]
- 计算 duration（按字数 ~300 字/分钟，最小 2 分钟）
- 全部为真实出版物原文，未做任何 AI 改写。
"""
import os, re, json
from ebooklib import epub
from bs4 import BeautifulSoup

APP = "G:/gpt/星橙故事铺腾讯/app"
EPW = "G:/gpt/星橙故事铺腾讯/新故事/安徒生童话）.epub"
MOB = "G:/gpt/星橙故事铺腾讯/新故事/王尔德童话.mobi"

FRONT = ["总目录","目录","译者序","前言","序言","作者序","说明","出版说明","传记","附录","后记","索引","安徒生传","关于"]
BOILER = ["掌上书苑","版权归原作者","仅供学习交流","下载后24小时","cnepub","制作上传","epub掌上书苑","www."]

def clean_para(t):
    return t.strip()

def strip_boiler(text):
    # 按行去掉页脚/版权行
    lines = text.split("\n")
    out = []
    for ln in lines:
        if any(b in ln for b in BOILER):
            continue
        out.append(ln)
    return "\n".join(out)

def doc_items(path):
    book = epub.read_epub(path)
    items = []
    for it in book.get_items():
        mt = getattr(it, "media_type", "") or ""
        name = it.get_name().lower()
        if mt in ("application/xhtml+xml","text/html","application/xhtml") or name.endswith((".xhtml",".html",".htm")):
            items.append(it)
    return items

# ---------------- 安徒生 ----------------
def extract_andersen():
    items = doc_items(EPW)
    # 按 part 基名分组
    groups = {}
    order = []
    for it in items:
        m = re.search(r"(part\d+)", it.get_name())
        if not m:
            continue
        base = m.group(1)
        if base not in groups:
            groups[base] = []; order.append(base)
        groups[base].append(it)
    tales = []
    for base in sorted(order, key=lambda b: int(re.search(r"\d+", b).group())):
        files = groups[base]
        # 取第一个文件的 h1 作为篇名
        first_html = files[0].get_content()
        fsoup = BeautifulSoup(first_html, "html.parser")
        h1 = fsoup.find(["h1","h2"])
        title = h1.get_text(strip=True) if h1 else ""
        if not title or any(f in title for f in FRONT):
            continue
        # 拼接全部文件正文
        paras = []
        for f in files:
            soup = BeautifulSoup(f.get_content(), "html.parser")
            for p in soup.find_all(["p","div"]):
                t = p.get_text(strip=True)
                if t:
                    paras.append(t)
        content = "\n".join(paras)
        content = strip_boiler(content)
        content = content.strip()
        if len(content) < 80:
            continue
        tales.append({
            "title": title, "content": content, "tag": "安徒生童话",
            "author": "汉斯·克里斯蒂安·安徒生", "culture": "丹麦", "country": "丹麦",
            "collection": "安徒生童话", "source": "安徒生童话.epub",
        })
    return tales

# ---------------- 王尔德 ----------------
WILDE_OPENINGS = [
    ("快乐王子",       "快乐王子的雕像高高地耸立在城市上空"),
    ("夜莺和玫瑰",     "她说过只要我送给她一些红玫瑰，她就愿意与我跳舞"),
    ("自私的巨人",     "每天下午，孩子们放学后总喜欢到巨人的花园里去玩耍"),
    ("忠诚的朋友",     "一天早晨，老河鼠从自己的洞中探出头来"),
    ("神奇的火箭",     "这声音来自一个高大的，模样傲慢的火箭"),
    ("少年国王",       "在加冕典礼的前一天晚上，少年国王"),
    ("小公主的生日",   "虽说她是一个真正的公主，一位西班牙公主"),
    ("渔夫和他的灵魂", "每天晚上年轻的渔夫都要出海去打鱼"),
    ("星孩",           "从前有两个穷苦的樵夫正穿越一个大松林往家赶路"),
]
WILDE_EN = {
    "快乐王子":"The Happy Prince","夜莺和玫瑰":"The Nightingale and the Rose",
    "自私的巨人":"The Selfish Giant","忠诚的朋友":"The Devoted Friend",
    "神奇的火箭":"The Remarkable Rocket","少年国王":"The Young King",
    "小公主的生日":"The Birthday of the Infanta","渔夫和他的灵魂":"The Fisherman and His Soul",
    "星孩":"The Star-Child",
}

def extract_wilde():
    import mobi
    tempdir, html_tmp = mobi.extract(MOB)
    raw = open(html_tmp, encoding="utf-8", errors="ignore").read()
    soup = BeautifulSoup(raw, "html.parser")
    paras = [p.get_text(strip=True) for p in soup.find_all("p")]
    paras = [p for p in paras if p]
    text = "\n".join(paras)
    # 计算每篇开头位置
    pos = []
    for title, anchor in WILDE_OPENINGS:
        i = text.find(anchor)
        if i < 0:
            raise RuntimeError("未找到王尔德篇目开头: " + title)
        pos.append(i)
    tales = []
    for k, (title, anchor) in enumerate(WILDE_OPENINGS):
        start = pos[k]
        end = pos[k+1] if k+1 < len(pos) else len(text)
        content = text[start:end]
        content = strip_boiler(content).strip()
        tales.append({
            "title": title, "content": content, "tag": "王尔德童话",
            "author": "奥斯卡·王尔德", "culture": "英国", "country": "英国",
            "collection": "王尔德童话", "source": "王尔德童话.mobi",
            "titleEn": WILDE_EN.get(title, ""),
        })
    return tales

def build_story(obj, idx, prefix):
    content = obj["content"]
    duration = max(2, (len(content) + 299) // 300)
    summary = content[:100].replace("\n", " ")
    s = {
        "id": "%s_%02d_%s" % (prefix, idx, obj["title"]),
        "title": obj["title"],
        "summary": summary,
        "content": content,
        "tags": [obj["tag"]],
        "country": obj["country"],
        "culture": obj["culture"],
        "author": obj["author"],
        "collection": obj["collection"],
        "source": obj["source"],
        "popularity": 4,
        "duration": duration,
        "ageMin": 8,
        "ageMax": 13,
        "safetyChecked": True,
        "version": "1.0.0",
    }
    if obj.get("titleEn"):
        s["titleEn"] = obj["titleEn"]
    return s

def main():
    andersen = extract_andersen()
    wilde = extract_wilde()
    print("安徒生 提取篇数:", len(andersen))
    print("王尔德 提取篇数:", len(wilde))
    stories = []
    for i, o in enumerate(andersen, 1):
        stories.append(build_story(o, i, "hca"))
    for i, o in enumerate(wilde, 1):
        stories.append(build_story(o, i, "wilde"))
    # 汇总
    ac = sum(len(s["content"]) for s in stories)
    print("合计篇数:", len(stories), "| 总字数:", ac)
    print("\n=== 安徒生篇目（标题 / 字数 / 分钟）===")
    for s in stories:
        if s["culture"] == "丹麦":
            print(f"  {s['title']}  | {len(s['content'])}字 | {s['duration']}分")
    print("\n=== 王尔德篇目 ===")
    for s in stories:
        if s["culture"] == "英国":
            print(f"  {s['title']}  | {len(s['content'])}字 | {s['duration']}分")
    # 写出
    out = os.path.join(APP, "js", "stories_data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.STORY_LIBRARY_EXT = ")
        f.write(json.dumps(stories, ensure_ascii=False, indent=0))
        f.write(";\n")
    print("\n已写出:", out, os.path.getsize(out), "bytes")

if __name__ == "__main__":
    main()
