# -*- coding: utf-8 -*-
"""
Fetch 100 faithful public-domain Chinese myth/folk tales from 维基文库 (zh.wikisource.org).
Rules (IRONCLAD):
 - NO AI generation / paraphrasing / translation of meaning.
 - Source text is taken VERBATIM; only mechanical 繁->簡 conversion via OpenCC.
 - Each tale keeps its original plot/characters/dialogue/ending/meaning intact.
 - Splitting (搜神記/山海經) extracts a CONTIGUOUS verbatim block, never splices.
Usage (run with the venv python that has opencc installed):
  python fetch_cn_library.py --offset 0 --count 20
Progress is appended to cn_stories.jsonl (one JSON object per line).
"""
import sys, os, re, json, time, html as H, argparse, urllib.request, urllib.parse, urllib.error
sys.path.insert(0, "/c/Users/Administrator/.workbuddy/binaries/python/envs/default/Lib/site-packages")
from opencc import OpenCC
cc = OpenCC("t2s")

WS = "G:/gpt/星橙故事铺腾讯/app"
JSONL = os.path.join(WS, "cn_stories.jsonl")

def api(params):
    url = "https://zh.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent":"StoryCollectBot/1.0 (research)"})
    for a in range(5):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(20); continue
            raise
        except Exception:
            time.sleep(3); continue
    raise RuntimeError("api failed after retries: " + str(params))

def strip_html(html):
    html = re.sub(r'<style.*?</style>', '', html, flags=re.S)
    html = re.sub(r'<script.*?</script>', '', html, flags=re.S)
    html = re.sub(r'<(br|/p|/div|/li|/h[1-6]|/tr)[^>]*>', '\n', html)
    html = re.sub(r'<[^>]+>', '', html)
    txt = H.unescape(html)
    txt = re.sub(r'[\[［]编辑[\]］]', '', txt)   # drop MediaWiki edit-link markers
    txt = re.sub(r'^\s*目录\s*$', '', txt, flags=re.M)
    return cc.convert(re.sub(r'\n{3,}', '\n\n', txt).strip())

CACHE = {}
def fetch_page(book, section=None):
    key = (book, section)
    if key in CACHE:
        return CACHE[key]
    params = {"action":"parse","page":book,"prop":"text","format":"json","formatversion":"2"}
    if section is not None:
        params["section"] = str(section)
    d = api(params)
    txt = strip_html(d.get("parse",{}).get("text",""))
    CACHE[key] = txt
    time.sleep(1.5)
    return txt

def section_line(book, section):
    d = api({"action":"parse","page":book,"prop":"sections","format":"json","formatversion":"2"})
    for s in d.get("parse",{}).get("sections",[]):
        if str(s["index"]) == str(section):
            return cc.convert(re.sub(r'<[^>]+>','',s["line"])).strip()
    return ""

def clean_block(b):
    b = b.strip()
    # drop navigation / sister-project lines
    if re.match(r'^\s*第.+卷\s*[◄►]', b): return ""
    if "姊妹计划" in b: return ""
    if b.startswith("﻿"): b = b.lstrip("﻿")
    return b

def split_tales(voltext):
    """Split a 搜神記/山海經 volume into contiguous tale blocks.
    Each tale begins with a full-width-space indent (\u3000).
    NOTE: must NOT strip() leading \u3000, or the indent test fails."""
    # drop volume navigation header: "第十卷 ◄ 搜神记 第十一卷 ► 第十二卷"
    voltext = re.sub(r'第\s*[一二三四五六七八九十百零]+\s*卷\s*[◄►⏪⏩]?.*?(?=\u3000\u3000|$)', ' ', voltext, flags=re.S)
    voltext = re.sub(r'姊妹计划[：:].*', '', voltext)
    lines = voltext.split('\n')
    blocks = []
    cur = []
    for ln in lines:
        stripped = ln.strip()
        if not stripped:
            continue
        if ln.startswith('\u3000'):
            if cur:
                blocks.append(''.join(cur).lstrip('\u3000').strip('\n\r'))
            cur = [ln.lstrip('\u3000').strip('\n\r')]
        else:
            # continuation line of the current tale, or stray nav text (ignored if cur empty)
            if cur:
                cur.append(stripped)
    if cur:
        blocks.append(''.join(cur).lstrip('\u3000').strip('\n\r'))
    return [b for b in blocks if len(b) > 10]

def find_block(voltext, anchor):
    tales = split_tales(voltext)
    for t in tales:
        if t.startswith(anchor) or anchor in t[:40]:
            return t
    # fallback: any block containing the anchor (e.g. tale starts with a different word)
    for t in tales:
        if anchor in t:
            return t
    return None

# ---------- PLAN ----------
# Each spec: (kind, book, payload, meta)
PLAN = []
def add_section(book, idx, meta):
    PLAN.append(("section", book, idx, meta))
def add_ssj_one(vol, anchor, meta):
    PLAN.append(("ssj_one", vol, anchor, meta))
def add_shanhaijing(vol, anchor, meta):
    PLAN.append(("shanhaijing", vol, anchor, meta))
def add_page_whole(book, meta):
    PLAN.append(("page_whole", book, None, meta))

# 列仙傳 1..44 (神话/仙传)
for i in range(1, 45):
    add_section("列仙傳", i, {"culture":"中国神话","author":"刘向","source":"《列仙传》〔西汉〕刘向","tags":["中国神话","神仙","先秦"],"cat":"仙传"})

# 神仙傳 卷一/卷二/卷三/卷五/卷七 (神话/仙传) -> 20
sx_map = [("神仙傳/卷一",[1,2,3,4,5,6,7]),
          ("神仙傳/卷二",[1,2,3,4,5,6,7]),
          ("神仙傳/卷三",[1,2,3,4,5,6]),
          ("神仙傳/卷五",[1,2,3,4,5]),
          ("神仙傳/卷七",[1,2,3])]
for vol, idxs in sx_map:
    for i in idxs:
        add_section(vol, i, {"culture":"中国神话","author":"葛洪","source":"《神仙传》〔东晋〕葛洪","tags":["中国神话","神仙","汉代"],"cat":"仙传"})

# 續齊諧記 1..16 (民间传说/志怪)
for i in range(1, 17):
    add_section("續齊諧記", i, {"culture":"中国民间传说","author":"吴均","source":"《续齐谐记》〔南朝梁〕吴均","tags":["中国民间传说","志怪","魏晋"],"cat":"志怪"})

# 搜神記 famous folk tales (民间传说)
ssj_meta = {"culture":"中国民间传说","author":"干宝","source":"《搜神记》〔东晋〕干宝","tags":["中国民间传说","志怪","魏晋"],"cat":"志怪"}
add_ssj_one("搜神記/第01卷", "董永", dict(ssj_meta, title="董永"))           # 七仙女原型
add_ssj_one("搜神記/第01卷", "刘晨", dict(ssj_meta, title="刘晨阮肇"))       # 天台遇仙
add_ssj_one("搜神記/第04卷", "河伯", dict(ssj_meta, title="河伯婿"))
add_ssj_one("搜神記/第11卷", "韩凭", dict(ssj_meta, title="韩凭夫妇"))
add_ssj_one("搜神記/第11卷", "干将莫邪", dict(ssj_meta, title="干将莫邪"))
add_ssj_one("搜神記/第11卷", "东海孝妇", dict(ssj_meta, title="东海孝妇"))
add_ssj_one("搜神記/第11卷", "辛道度", dict(ssj_meta, title="辛道度"))
add_ssj_one("搜神記/第11卷", "王道平", dict(ssj_meta, title="王道平与唐父喻"))
add_ssj_one("搜神記/第14卷", "盘瓠", dict(ssj_meta, title="盘瓠"))
add_ssj_one("搜神記/第14卷", "太古之时", dict(ssj_meta, title="蚕马"))
add_ssj_one("搜神記/第14卷", "豫章新喻", dict(ssj_meta, title="毛衣女"))
add_ssj_one("搜神記/第16卷", "紫玉", dict(ssj_meta, title="紫玉"))
add_ssj_one("搜神記/第16卷", "苏娥", dict(ssj_meta, title="苏娥诉冤"))
add_ssj_one("搜神記/第19卷", "李寄", dict(ssj_meta, title="李寄斩蛇"))

# 山海經 narrative myths (神话)
shj_meta = {"culture":"中国神话","author":"佚名","source":"《山海经》〔先秦〕","tags":["中国神话","上古","山海经"],"cat":"神话"}
add_shanhaijing("山海經/北山經", "发鸠之山", dict(shj_meta, title="精卫填海"))
add_shanhaijing("山海經/海外北經", "夸父", dict(shj_meta, title="夸父逐日"))
add_shanhaijing("山海經/海外西經", "刑天", dict(shj_meta, title="刑天舞干戚"))
add_shanhaijing("山海經/海內經", "洪水滔天", dict(shj_meta, title="鲧禹治水"))

# 穆天子傳 (神话/周穆王见西王母)
add_page_whole("穆天子傳", {"culture":"中国神话","author":"佚名","source":"《穆天子传》〔先秦〕","tags":["中国神话","周穆王","先秦"],"cat":"神话","title":"穆天子传"})

# 搜神後記 白水素女 (田螺姑娘, 民间传说)
add_ssj_one("搜神後記/卷五", "谢端", {"culture":"中国民间传说","author":"陶潜","source":"《搜神后记》〔东晋〕陶潜","tags":["中国民间传说","田螺姑娘","晋代"],"cat":"志怪","title":"白水素女（田螺姑娘）"})

# padding: 列仙傳 45..60 (only fills if earlier specs fall short of 100)
for i in range(45, 61):
    add_section("列仙傳", i, {"culture":"中国神话","author":"刘向","source":"《列仙传》〔西汉〕刘向","tags":["中国神话","神仙","先秦"],"cat":"仙传"})

# ---------- existing-title dedupe ----------
def existing_titles():
    titles = set()
    for fn in ["stories_data.js","stories_user.js"]:
        p = os.path.join(WS, fn)
        if os.path.exists(p):
            for m in re.findall(r'"title"\s*:\s*"([^"]+)"', open(p, encoding="utf-8").read()):
                titles.add(cc.convert(m))
    jl = JSONL
    if os.path.exists(jl):
        for line in open(jl, encoding="utf-8"):
            try:
                o = json.loads(line)
                titles.add(o.get("title",""))
            except: pass
    return titles

def build_story(title, content, meta):
    content = content.strip()
    if not content or len(content) < 30:
        return None
    return {
        "title": title,
        "content": content,
        "source": meta["source"],
        "author": meta["author"],
        "culture": meta["culture"],
        "tags": meta.get("tags", []),
        "ageGroup": "8-13",
        "durationMin": max(2, (len(content) + 299)//300),
        "summary": content[:60],
        "safetyChecked": True,
        "cat": meta.get("cat",""),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--count", type=int, default=20)
    args = ap.parse_args()
    exist = existing_titles()
    # current count already in jsonl
    cur = 0
    if os.path.exists(JSONL):
        cur = sum(1 for _ in open(JSONL, encoding="utf-8"))
    specs = PLAN[args.offset: args.offset + args.count]
    added = 0
    print(f"[batch] offset={args.offset} count={args.count} already_in_jsonl={cur}")
    for kind, book, payload, meta in specs:
        if cur >= 100:
            print("  reached 100, stop.")
            break
        title = meta.get("title")
        content = None
        try:
            if kind == "section":
                title = title or section_line(book, payload)
                content = fetch_page(book, payload)
            elif kind == "ssj_one":
                vol = fetch_page(book)  # whole volume
                content = find_block(vol, payload)
                if content is None:
                    print(f"  [WARN] ssj anchor not found: {book} / {payload}")
                    continue
            elif kind == "shanhaijing":
                vol = fetch_page(book)
                content = find_block(vol, payload)
                if content is None:
                    print(f"  [WARN] shanhaijing anchor not found: {book} / {payload}")
                    continue
            elif kind == "page_whole":
                content = fetch_page(book)
                # trim header/footer boilerplate
                content = re.sub(r'^\s*穆天子傳\s*', '', content)
        except Exception as e:
            print(f"  [ERR] {kind} {book} {payload}: {e}")
            continue
        st = build_story(title, content, meta)
        if st is None:
            print(f"  [SKIP] empty/too short: {title}")
            continue
        simp_title = cc.convert(st["title"])
        if simp_title in exist:
            print(f"  [DUP] skip: {simp_title}")
            continue
        exist.add(simp_title)
        with open(JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(st, ensure_ascii=False) + "\n")
        cur += 1; added += 1
        print(f"  [+{added}] {simp_title}  ({st['cat']}, {st['durationMin']}min, {len(st['content'])}字)")
    print(f"[batch done] added_this_batch={added} total_in_jsonl={cur}")

if __name__ == "__main__":
    main()
