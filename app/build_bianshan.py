# -*- coding: utf-8 -*-
"""
从《边山狩猎》(梁泊 著，少年儿童出版社) txt 直提真实正文，追加进 stories_data.js。

规则：
- 只做原文直提，严禁任何 AI 生成/改写。
- 只在 stories_data.js 末尾 `];` 前追加，不重写全文。
- 顺带清理 2 条历史噪声条目（版权页/目录页，非故事）。
"""
import re, os, json, shutil, math

SRC = "D:/admin/Downloads/边山狩猎.txt"
LIB = "G:/gpt/星橙故事铺腾讯/app/js/stories_data.js"
BAK = LIB + ".bak_bianshan"

COLLECTION = "边山狩猎"
AUTHOR = "梁泊"
SOURCE = "边山狩猎.txt"

# ---------- 1. 读取并切分 ----------
raw = open(SRC, encoding="utf-8").read()
body = raw[raw.find("【"):]          # 跳过书名/作者/内容提要/目录
parts = re.split(r"【([^】]+)】", body)
assert len(parts) == 41, "expected 20 chapters, got %d" % ((len(parts) - 1) // 2)

stories = []
for i in range(1, len(parts), 2):
    title = parts[i].strip()
    c = parts[i + 1]
    c = re.sub(r"={5,}", "", c)                      # 去掉 ==== 分隔线
    lines = [l.strip() for l in c.split("\n")]
    lines = [l for l in lines if l]
    c = "\n".join(lines)
    # 噪声过滤：版权页 / 目录页 / 广告
    if re.search(r"图书在版编目|ISBN|版权所有|http://|www\.|z-library", c):
        print("  [skip noise]", title)
        continue
    if len(c) < 200:
        print("  [skip short]", title)
        continue
    stories.append((title, c))

print("提取篇数:", len(stories))

# ---------- 2. 读库，去重 ----------
lib = open(LIB, encoding="utf-8").read()
data = json.loads(lib[lib.index("["):lib.rindex("]") + 1])
print("库内现有:", len(data))
exist = set(x["title"].strip() for x in data)
dup = [t for t, _ in stories if t in exist]
if dup:
    print("与库内重复，跳过:", dup)
stories = [(t, c) for t, c in stories if t not in exist]
print("去重后新增:", len(stories))
assert stories, "no new stories"

# ---------- 3. 清理历史噪声条目（版权页/目录页，非故事） ----------
NOISE_IDS = [
    "xbz_131_Desconocido",   # 小巴掌童话 版权页(CIP)
]
NOISE_TITLE_COLLECTION = [
    ("第1则", "中国童话"),     # 中国童话 版权页+总目录
]


def find_object_span(text, id_value):
    """返回 (start, end) 覆盖整个 {..} 对象，含字符串感知"""
    key = '"id": "%s"' % id_value
    k = text.find(key)
    if k == -1:
        return None
    s = text.rfind("{", 0, k)
    depth = 0
    in_str = False
    esc = False
    for j in range(s, len(text)):
        ch = text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return (s, j + 1)
    return None


def remove_object(text, id_value):
    """删除整个 {..} 对象，并正确处理它前后多余的逗号，保证结果仍是合法 JSON 数组。"""
    sp = find_object_span(text, id_value)
    if not sp:
        return text, False
    s, e = sp

    # 情形 A：后面紧跟逗号（非末尾元素）→ 连逗号一起删
    j = e
    while j < len(text) and text[j] in "\n\r \t":
        j += 1
    if j < len(text) and text[j] == ",":
        j += 1
        while j < len(text) and text[j] in "\n\r \t":
            j += 1
        return text[:s] + text[j:], True

    # 情形 B：它是最后一个元素 → 删掉它前面的逗号
    i = s - 1
    while i >= 0 and text[i] in "\n\r \t":
        i -= 1
    if i >= 0 and text[i] == ",":
        return text[:i] + text[e:], True

    # 情形 C：唯一元素
    return text[:s] + text[e:], True


for nid in NOISE_IDS:
    lib, ok = remove_object(lib, nid)
    print("清理噪声条目 %-22s %s" % (nid, "OK" if ok else "未找到"))

# 按 (title, collection) 清理（无稳定 id 时用）
for tt, cc in NOISE_TITLE_COLLECTION:
    tmp = json.loads(lib[lib.index("["):lib.rindex("]") + 1])
    hit = [x for x in tmp if x["title"] == tt and x["collection"] == cc]
    for x in hit:
        lib, ok = remove_object(lib, x["id"])
        print("清理噪声条目 %-22s %s" % (x["id"], "OK" if ok else "未找到"))

# 校验清理结果
chk = json.loads(lib[lib.index("["):lib.rindex("]") + 1])
print("清理后库内:", len(chk))
assert not [x for x in chk if x["title"] == "Desconocido"], "Desconocido 仍在"
assert not [x for x in chk if x["collection"] == "中国童话" and x["title"] == "第1则"], "中国童话第1则仍在"

# ---------- 4. 生成新条目 ----------
def make_summary(c, limit=120):
    s = c.replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= limit:
        return s
    cut = s[:limit]
    p = max(cut.rfind("。"), cut.rfind("！"), cut.rfind("？"))
    return (cut[:p + 1] if p > 40 else cut).strip()


objs = []
for idx, (title, c) in enumerate(stories, 1):
    safe = re.sub(r"[^\w\u4e00-\u9fff]", "", title)[:12] or ("p%03d" % idx)
    o = {
        "id": "bsls_%03d_%s" % (idx, safe),
        "title": title,
        "summary": make_summary(c),
        "content": c,
        "tags": [COLLECTION],
        "country": "中国",
        "culture": "中国",
        "author": AUTHOR,
        "collection": COLLECTION,
        "source": SOURCE,
        "popularity": 4,
        "duration": max(1, round(len(c) / 300)),
        "ageMin": 8,
        "ageMax": 13,
        "safetyChecked": True,
        "version": "1.0.0",
    }
    objs.append(o)

# ---------- 5. 追加（不重写全文） ----------
tail = "\n}];"
pos = lib.rindex(tail) + 2   # 跳过 "\n}"，停在最后一个旧对象的闭合括号之后
add = ",\n" + ",\n".join(json.dumps(o, ensure_ascii=False, indent=2) for o in objs)
new = lib[:pos] + add + lib[pos:]

# ---------- 6. 写回 ----------
shutil.copyfile(LIB, BAK)
open(LIB, "w", encoding="utf-8", newline="\n").write(new)

# ---------- 7. 校验 ----------
final = json.loads(new[new.index("["):new.rindex("]") + 1])
import collections
print()
print("=== 结果 ===")
print("最终篇数:", len(final))
c = collections.Counter(x["collection"] for x in final)
for k, v in c.most_common():
    print("  %s: %d" % (k, v))
nb = [x for x in final if x["collection"] == COLLECTION]
print("新增篇数:", len(nb))
lens = [len(x["content"]) for x in nb]
print("字数 中位%d 最短%d 最长%d 合计%d" % (
    sorted(lens)[len(lens) // 2], min(lens), max(lens), sum(lens)))
for x in nb[:3]:
    print("  [%d字 %d分钟] %s" % (len(x["content"]), x["duration"], x["title"]))
print("备份:", BAK)
