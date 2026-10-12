# -*- coding: utf-8 -*-
"""
从用户提供的张秋生《小巴掌童话》EPUB 中提取真实故事文本，追加进 stories_data.js。

铁律：只做「原书文本抽取」，不改写、不续写、不生成任何句子。
"""
import zipfile, re, html, json, os, sys, collections

APP = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(APP, "js", "stories_data.js")

BOOK1 = "D:/admin/Downloads/18167-国内大奖书系：小巴掌童话3（注音全彩美绘）/小巴掌童话套装1-6册_(张秋生)_(z-library.sk,_1lib.sk,_z-lib.sk).epub"
BOOK2 = "D:/admin/Downloads/18167-国内大奖书系：小巴掌童话3（注音全彩美绘）/国内大奖书系：小巴掌童话3（注音全彩美绘）.epub"

COLLECTION = "小巴掌童话"
AUTHOR = "张秋生"

NOISE = re.compile(r"ePUBw|z-library|1lib|Epubor|www\.|http|免责声明|购书|扫码|关注公众号")


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def norm(s):
    return re.sub(r"\s+", " ", strip_tags(s)).strip()


def clean_title(t):
    """去掉 '3.' / '3．' / '三、' 之类序号前缀"""
    t = norm(t)
    t = re.sub(r"^\s*\d+\s*[.．、]\s*", "", t)
    t = re.sub(r"^[一二三四五六七八九十百]+\s*[、.．]\s*", "", t)
    return t.strip()


def extract_book1(path):
    """套装：h2.bodycontent-first-title + p.bodycontent-text"""
    z = zipfile.ZipFile(path)
    files = [n for n in z.namelist() if re.search(r"text\d+\.html$", n)]
    files.sort(key=lambda x: int(re.search(r"(\d+)", x.split("/")[-1]).group(1)))
    out = []
    for f in files:
        raw = z.read(f).decode("utf-8", "replace")
        if "<title>Contents</title>" in raw:      # 目录页
            continue
        mt = re.search(r'<h2 class="bodycontent-first-title">(.*?)</h2>', raw, re.S)
        if not mt:
            continue
        title = clean_title(mt.group(1))
        paras = [norm(p) for p in re.findall(r'<p class="bodycontent-text">(.*?)</p>', raw, re.S)]
        paras = [p for p in paras if p]
        body = "\n".join(paras).strip()
        if title and len(body) >= 120:
            out.append((title, body))
    return out


def extract_book2(path):
    """单本：h1.titlepage / h2.titlepage，正文 p 段落"""
    z = zipfile.ZipFile(path)
    files = [n for n in z.namelist() if n.endswith((".html", ".xhtml"))]
    out = []
    for f in files:
        raw = z.read(f).decode("utf-8", "replace")
        mt = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S)
        if not mt:
            continue
        title = clean_title(mt.group(1))
        if not title or title in ("Contents", "目录", "封面", "版权信息"):
            continue
        bodyraw = re.search(r"<body[^>]*>(.*)</body>", raw, re.S)
        bodyraw = bodyraw.group(1) if bodyraw else raw
        paras = [norm(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", bodyraw, re.S)]
        paras = [p for p in paras if p]
        if paras and norm(paras[0]) == title:     # 正文首段重复标题
            paras = paras[1:]
        body = "\n".join(paras).strip()
        if title and len(body) >= 120:
            out.append((title, body))
    return out


def make_summary(body, limit=90):
    """summary 取正文开头；与既有库的风格一致"""
    s = body.replace("\n", " ")
    if len(s) <= limit:
        return s
    cut = s[:limit]
    for p in ("。", "！", "？", "；"):
        i = cut.rfind(p)
        if i > limit * 0.5:
            return cut[: i + 1]
    return cut + "…"


def estimate_duration(n):
    """中文朗读约 300 字/分钟，至少 1 分钟"""
    return max(1, round(n / 300.0))


def main():
    raw_items = []
    src_stat = collections.OrderedDict()

    for path, fn, label in ((BOOK1, extract_book1, "套装1-6册"), (BOOK2, extract_book2, "单本第3册")):
        if not os.path.exists(path):
            print("[跳过] 找不到", path)
            continue
        got = fn(path)
        src_stat[label] = len(got)
        raw_items.extend(got)

    print("== 原始抽取 ==")
    for k, v in src_stat.items():
        print("   %s: %d 篇" % (k, v))

    # ---- 读取现有库，建立去重基线 ----
    raw = open(DATA, encoding="utf-8").read()
    s, e = raw.index("["), raw.rindex("]") + 1
    lib = json.loads(raw[s:e])
    exist_titles = set(d["title"] for d in lib)
    print("\n现有库: %d 篇" % len(lib))

    # ---- 清洗：去噪声、去重、排序 ----
    seen, items, dropped_noise, dropped_dup, dropped_lib = set(), [], 0, 0, 0
    for title, body in raw_items:
        if NOISE.search(body):
            body = NOISE.sub("", body)
            dropped_noise += 1
        if title in exist_titles:
            dropped_lib += 1
            continue
        if title in seen:
            dropped_dup += 1
            continue
        seen.add(title)
        exist_titles.add(title)
        items.append((title, body))

    print("\n== 清洗 ==")
    print("   噪声过滤: %d | 与现有库重名: %d | 内部重复: %d | 最终采纳: %d"
          % (dropped_noise, dropped_lib, dropped_dup, len(items)))

    if not items:
        print("\n没有新增故事，退出。")
        return

    # ---- 生成条目 ----
    new = []
    for i, (title, body) in enumerate(items, 1):
        new.append({
            "id": "xbz_%03d_%s" % (i, title),
            "title": title,
            "summary": make_summary(body),
            "content": body,
            "tags": [COLLECTION],
            "country": "中国",
            "culture": "中国",
            "author": AUTHOR,
            "collection": COLLECTION,
            "source": "小巴掌童话套装1-6册.epub",
            "popularity": 4,
            "duration": estimate_duration(len(body)),
            "ageMin": 6,
            "ageMax": 12,
            "safetyChecked": True,
            "version": "1.0.0",
        })

    # ---- 追加写回（保留原有字节布局，仅在末尾 '];' 前插入）----
    head = raw[: raw.rindex("]")]
    if not head.endswith("}\n"):
        head = head.rstrip() + "\n"
    buf = [head]
    for obj in new:
        body_txt = ",\n".join(
            '  %s' % json.dumps(k, ensure_ascii=False) + ": " + json.dumps(v, ensure_ascii=False)
            for k, v in obj.items()
        )
        buf.append(",\n{\n" + body_txt + "\n}")

    tail = raw[raw.rindex("]"):]
    buf.append(tail if tail.endswith("\n") else tail + "\n")
    open(DATA, "w", encoding="utf-8").write("".join(buf))

    lens = [len(o["content"]) for o in new]
    print("\n== 写回完成 ==")
    print("   新增 %d 篇，总库 %d 篇" % (len(new), len(lib) + len(new)))
    print("   字数 min/中位/max: %d/%d/%d" % (min(lens), sorted(lens)[len(lens) // 2], max(lens)))
    print("   时长分布:", dict(sorted(collections.Counter(o["duration"] for o in new).items())))
    print("\n前 8 篇:")
    for o in new[:8]:
        print("   [%4d字/%2d分] %s" % (len(o["content"]), o["duration"], o["title"]))


if __name__ == "__main__":
    main()
