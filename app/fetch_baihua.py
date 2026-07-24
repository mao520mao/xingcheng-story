# -*- coding: utf-8 -*-
"""对 CN / 历史趣事 检测文言文，并从维基百科抓取真实白话全文替换（非 AI 生成）。
输出 baihua_map.jsonl: {"file","title","baihua","baihua_src","status"}
status: ok(已抓到白话) / no_source(维基百科无对应词条) / err(网络错误)
"""
import os, json, time, urllib.request, urllib.parse

WS = "G:/gpt/星橙故事铺腾讯/app"
FILES = {
    "cn": os.path.join(WS, "cn_stories.jsonl"),
    "history": os.path.join(WS, "history_stories.jsonl"),
}
OUT = os.path.join(WS, "baihua_map.jsonl")

# 历史趣事中为「轶事标题」，需映射到维基百科人物词条
HISTORY_WIKI_MAP = {
    "张良圯上受书": "张良",
    "江革行佣供母": "江革",
    "颜真卿祭侄文稿": "颜真卿",
    "郭子仪单骑退回纥": "郭子仪",
    "朱熹鹅湖之会": "朱熹",
    "张载横渠四句": "张载",
}

CLASSICAL = ["之","乎","者","也","矣","焉","哉","兮","夫","盖","遂","辄","尝","曰","吾","汝","尔","其","故","乃"]
MODERN = ["的","了","吗","呢","吧","把","被","着","我们","他们","现在","因为","所以","但是","就","这","那","他","她"]

def density(t, chars):
    n = sum(t.count(c) for c in chars)
    return round(n * 1000 / max(1, len(t)), 1)

def is_classical(text):
    g = density(text, CLASSICAL)
    m = density(text, MODERN)
    return g > 15 and m < 10

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")

def wiki_extract(title):
    api = ("https://zh.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1"
           "&titles=" + urllib.parse.quote(title) + "&format=json&redirects=1")
    try:
        d = json.loads(fetch(api))
        p = list(d["query"]["pages"].values())[0]
        if "missing" in p:
            return None, title
        return p.get("extract", ""), title
    except Exception as e:
        return "ERR:" + str(e)[:40], title

def get_baihua(file_key, title):
    # 先按原标题试，再按历史人名映射试
    candidates = [title]
    if file_key == "history" and title in HISTORY_WIKI_MAP:
        candidates.append(HISTORY_WIKI_MAP[title])
    for cand in candidates:
        ex, used = wiki_extract(cand)
        if ex and not ex.startswith("ERR") and len(ex) >= 120:
            return ex.strip(), used
        if ex == "ERR:HTTP Error 429":
            # 退避后重试同候选
            time.sleep(15)
            ex2, used2 = wiki_extract(cand)
            if ex2 and not ex2.startswith("ERR") and len(ex2) >= 120:
                return ex2.strip(), used2
    return None, candidates[-1]

rows_out = []
total = 0
n_classical = 0
n_ok = 0
n_no = 0
n_err = 0

for fk, path in FILES.items():
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    for r in rows:
        total += 1
        title = r["title"]
        content = r.get("content", "")
        if not is_classical(content):
            rows_out.append({"file": fk, "title": title, "baihua": "", "baihua_src": "", "status": "not_classical"})
            continue
        n_classical += 1
        baihua, src = get_baihua(fk, title)
        if baihua:
            rows_out.append({"file": fk, "title": title, "baihua": baihua, "baihua_src": src, "status": "ok"})
            n_ok += 1
            print(f"[ok] {fk}/{title} <- 维基百科《{src}》({len(baihua)}字)")
        elif baihua is None and src:
            rows_out.append({"file": fk, "title": title, "baihua": "", "baihua_src": src, "status": "no_source"})
            n_no += 1
            print(f"[no_source] {fk}/{title} (维基百科无《{src}》)")
        else:
            rows_out.append({"file": fk, "title": title, "baihua": "", "baihua_src": "", "status": "err"})
            n_err += 1
            print(f"[err] {fk}/{title}")
        time.sleep(1.0)  # 限流

with open(OUT, "w", encoding="utf-8") as f:
    for o in rows_out:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")

print("\n===== 汇总 =====")
print(f"扫描总数: {total} | 文言文命中: {n_classical}")
print(f"已替换为白话: {n_ok} | 无来源保留文言文: {n_no} | 错误: {n_err}")
print("map ->", OUT)
