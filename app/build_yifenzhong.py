# -*- coding: utf-8 -*-
"""
《一分钟破案（带谜底版）》提取脚本

源：D:/admin/Downloads/一分钟破案_带谜底版.txt （扫描版整理，UTF-8，49389 字）
原著：张祥斌 编写，浙江少年儿童出版社 2018（中国少年儿童智力挑战全书）

源文件结构：
  0~46    封面 / 说明 / 版权 CIP / 序          -> 丢弃
  47~172  【原书目录】（带【章】前缀）          -> 丢弃（仅用于校验篇数=119）
  174~    正文
          【第一章 伪证和谎言】                 -> 章分隔，不生成条目
          【张飞审瓜】                          -> 案例标题
          ZHANGFEI SHEN GUA                    -> 拼音行，丢弃
          案情正文若干段……
          【谜底】
          答案正文若干段……

用法：python build_yifenzhong.py          # 干跑，只打印统计
      python build_yifenzhong.py --write  # 真正追加进 stories_data.js
"""
import json, os, re, shutil, sys

SRC = "D:/admin/Downloads/一分钟破案_带谜底版.txt"
LIB = "G:/gpt/星橙故事铺腾讯/app/js/stories_data.js"
BOOK = "一分钟破案"
AUTHOR = "张祥斌"
PFX = "yfp"
WRITE = "--write" in sys.argv

# ---------- 1. 切分正文 ----------
raw = open(SRC, encoding="utf-8").read()
lines = raw.split("\n")

# 目录区：以【章】开头的行（用于校验篇数）
dir_items = []
for l in lines:
    if l.startswith("【章】"):
        continue
    m = re.match(r"^(.+?)\s+(\d+)$", l.strip())
    if m and 47 <= lines.index(l) <= 172:
        dir_items.append(m.group(1).strip())

CHAP_RE = re.compile(r"^【第[一二三四五六七八九十]+章.*】$")
def is_chapter(l):
    return bool(CHAP_RE.match(l.strip()))

def is_title(l):
    s = l.strip()
    return s.startswith("【") and s.endswith("】") and not is_chapter(s)

def has_cn(s):
    return bool(re.search(r"[\u4e00-\u9fff]", s))

# 找正文起点：第一个章标题行
start = None
for i, l in enumerate(lines):
    if is_chapter(l):
        start = i
        break
if start is None:
    raise SystemExit("找不到正文起点")

cases = []          # [{title, body:[...], answer:[...], chap}]
cur = None
mode = None         # 'body' | 'answer'
for l in lines[start:]:
    s = l.strip()
    if not s:
        continue
    if is_chapter(s):
        cur = None
        continue
    if s == "【谜底】":          # 必须先于 is_title 判断，否则会被当成案例标题
        mode = "answer"
        continue
    if is_title(s):
        cur = {"title": s[1:-1].strip(), "body": [], "answer": []}
        cases.append(cur)
        mode = "body"
        continue
    if cur is None:
        continue
    if not has_cn(s):          # 拼音行（ZHANGFEI SHEN GUA）
        continue
    if mode == "answer":
        cur["answer"].append(s)
    else:
        cur["body"].append(s)

# ---------- 2. 组装条目 ----------
# 纯「看图题」剔除清单：原书答案必须对照插图才能得出，App 无图则读者无从思考，
# 直接看答案体验极差。逐条人工复核后确定（2026-10-12）。
DROP = {
    "找出小偷",       # 四选一影子图，且原文本身就缺谜底
    "正确的背影",     # 四张背影照片选一张，谜底仅"3号图"
    "相同的咖啡杯",   # 四选一咖啡杯俯拍图，谜底仅"2号咖啡杯"
    "找小偷",         # 六张毛绒玩具合影找共同出现者，谜底"穿绿衣服的小熊"
    "奇妙的梳妆台",   # A/B 两幅镜像图二选一，"请看右页图"
    "奇怪的家书",     # 画谜，信纸上的画未以文字描述
    "不明飞行物",     # 需辨认夜空照片中哪一点是 UFO
    "恶劣的珠宝商人", # "请你先数数图中的珠子"，项链分叉结构无文字描述
    "黑手党的枪战",   # 七人站位与瞄准关系全在图上
    "隐蔽的住所",     # A/B/C/D 四座房子朝向图
}

def build(c, idx):
    body = "\n".join(c["body"]).strip()
    ans = "\n".join(c["answer"]).strip()
    if ans:
        content = body + "\n\n【谜底】\n" + ans
    else:
        content = body
    # summary：案情首段，截断
    first = c["body"][0] if c["body"] else ""
    summ = first[:78] + ("…" if len(first) > 78 else "")
    dur = max(1, round(len(content) / 300))
    return {
        "id": "%s_%03d_%s" % (PFX, idx, c["title"]),
        "title": c["title"],
        "summary": summ,
        "content": content,
        "tags": [BOOK],
        "country": "中国",
        "culture": "中国",
        "author": AUTHOR,
        "collection": BOOK,
        "source": os.path.basename(SRC),
        "popularity": 4,
        "duration": dur,
        "ageMin": 8,
        "ageMax": 13,
        "safetyChecked": True,
        "version": "1.0.0",
    }

raw_count = len(cases)
cases = [c for c in cases if c["title"] not in DROP]
objs = [build(c, i + 1) for i, c in enumerate(cases)]

# ---------- 3. 校验（写回之前全部做完） ----------
report = []
report.append("目录条目数（用于比对）: %d" % len(dir_items))
report.append("原始案例数: %d" % raw_count)
report.append("剔除看图题: %d -> %s" % (len(DROP), sorted(DROP)))
report.append("入库案例数: %d" % len(objs))

# 3.1 无谜底
noans = [o["title"] for o in objs if "【谜底】" not in o["content"]]
report.append("缺谜底: %d %s" % (len(noans), noans[:10]))

# 3.2 过短
short = [(o["title"], len(o["content"])) for o in objs if len(o["content"]) < 120]
report.append("正文<120字: %d %s" % (len(short), short[:10]))

# 3.3 噪声（CIP / ISBN / 出版 / 责任编辑 / 扫一扫）
NOISE = ["图书在版编目", "ISBN", "责任编辑", "责任印制", "开本", "印张", "定价", "扫一扫", "z-library", "ePUBw"]
noise = [(o["title"], k) for o in objs for k in NOISE if k in o["content"]]
report.append("命中噪声: %d %s" % (len(noise), noise[:20]))

# 3.4 标题重复
seen, dup = set(), []
for o in objs:
    if o["title"] in seen:
        dup.append(o["title"])
    seen.add(o["title"])
report.append("标题重复: %d %s" % (len(dup), dup[:10]))

# 3.5 依赖插图（正文里出现（插图/（整页插图 —— 没图就答不出来，需人工复核）
illus = [o["title"] for o in objs if "（插图" in o["content"] or "（整页插图" in o["content"]]
report.append("含插图说明: %d" % len(illus))
report.append("  " + " / ".join(illus))

# 3.6 字数统计
lens = sorted(len(o["content"]) for o in objs)
report.append("字数: min=%d 中位=%d max=%d 合计=%d" % (
    lens[0], lens[len(lens) // 2], lens[-1], sum(lens)))
report.append("duration 分布: %s" % sorted(set(o["duration"] for o in objs)))

# 3.7 与库内已有标题去重
lib = open(LIB, encoding="utf-8").read()
data = json.loads(lib[lib.index("["): lib.rindex("]") + 1])
existing = set(x["title"] for x in data)
report.append("库内现有: %d 篇" % len(data))
conflict = [o["title"] for o in objs if o["title"] in existing]
report.append("与库内标题冲突: %d %s" % (len(conflict), conflict[:10]))
idal = set(x["id"] for x in data)
report.append("id 冲突: %d" % sum(1 for o in objs if o["id"] in idal))

open("G:/gpt/星橙故事铺腾讯/app/_report_yfp.txt", "w", encoding="utf-8").write("\n".join(report))

if not WRITE:
    print("DRY RUN -> see _report_yfp.txt")
    raise SystemExit(0)

# ---------- 4. 写回（末尾追加，绝不重写全文） ----------
tail = "\n}];"
if not lib.endswith(tail + "\n") and not lib.endswith(tail):
    raise SystemExit("文件尾部形态不符，已中止（当前结尾: %r）" % lib[-12:])
pos = lib.rindex(tail) + 2     # 停在旧对象闭合 } 之后
add = ",\n" + ",\n".join(json.dumps(o, ensure_ascii=False, indent=2) for o in objs)
shutil.copyfile(LIB, LIB + ".bak_yifenzhong")
new = lib[:pos] + add + lib[pos:]
open(LIB, "w", encoding="utf-8").write(new)

# ---------- 5. 写后校验 ----------
chk = open(LIB, encoding="utf-8").read()
d2 = json.loads(chk[chk.index("["): chk.rindex("]") + 1])
from collections import Counter
c = Counter(x["collection"] for x in d2)
open("G:/gpt/星橙故事铺腾讯/app/_report_yfp.txt", "a", encoding="utf-8").write(
    "\n--- WRITE OK ---\n总篇数: %d\n一分钟破案: %d\n" % (len(d2), c.get(BOOK, 0)))
print("WRITTEN")
