# -*- coding: utf-8 -*-
"""用 playwright 真实浏览器突破百度百科反爬，抓真实白话正文替换文言文。
白话来源 = 百度百科词条正文（真人编写，非 AI）。
仅处理"纯文言文"篇目（g>35 且 m<4）。失败条目会被重试（不永久跳过）。
"""
import os, re, json, sys
from playwright.sync_api import sync_playwright

WS = "G:/gpt/星橙故事铺腾讯/app"
LIMIT = int(os.environ.get("PW_LIMIT", "999"))
SLEEP = 1.8
WAIT = 3500  # 渲染等待(ms)

def load_js(p):
    t = open(p, encoding="utf-8").read()
    m = re.search(r"=\s*(\[.*\])\s*;", t, re.S)
    if not m:
        m = re.search(r"window\.\w+\s*=\s*(\[.*\])\s*;", t, re.S)
    return json.loads(m.group(1))

CL = ['之','乎','者','也','矣','焉','哉','兮','夫','盖','遂','辄','尝','曰','吾','汝','尔','其','君','然','故','乃']
MD = ['的','了','吗','呢','吧','把','被','着','我们','他们','现在','因为','所以','但是','就','这','那','他','她','你']
def dens(t, c):
    n = sum(t.count(x) for x in c); return round(n*1000/max(1,len(t)),1)
def is_pure_cl(c):
    g = dens(c, CL); m = dens(c, MD); return g > 35 and m < 4
def is_baihua(t):
    # 白话判定：现代词密度>=2.5 且 总字数>=50 且 非纯古典
    g = dens(t, CL); m = dens(t, MD)
    return len(t) >= 50 and (m >= 2.5 or g < 25)

def extract_baike(pg):
    """从已加载的百度百科词条页提取白话正文。优先 main 内容区纯文本。"""
    # 主条目正文容器
    txt = ""
    try:
        el = pg.query_selector("div.J-lemma-content, div.lemmaWgt-lemmaContent, main")
        if el:
            txt = el.inner_text()
    except Exception:
        pass
    if not txt:
        parts = []
        for sel in [".lemma-summary", ".para"]:
            for p in pg.query_selector_all(sel)[:8]:
                try: parts.append(p.inner_text())
                except: pass
        txt = "\n".join(x.strip() for x in parts if x and len(x.strip()) > 1)
    # 清洗：去超长空白、去明显目录噪声
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    txt = "\n".join(lines)
    # 截取前 ~1400 字（够故事正文，避免抓到参考资料区）
    return txt[:1400].strip()

def main():
    cn = load_js(os.path.join(WS, "js/stories_cn.js"))
    hist = load_js(os.path.join(WS, "js/stories_history.js"))
    targets = []
    for s in cn:
        if is_pure_cl(s.get("content", "")):
            targets.append(("cn", s["title"]))
    for s in hist:
        if is_pure_cl(s.get("content", "")):
            targets.append(("history", s["title"]))
    print("纯文言篇数:", len(targets))
    targets = targets[:LIMIT]
    print("本次处理:", len(targets))

    out = os.path.join(WS, "baihua_map_pw.jsonl")
    ok_done = set()   # 仅 ok 的跳过；fail 重试
    if os.path.exists(out):
        for l in open(out, encoding="utf-8"):
            l = l.strip()
            if not l: continue
            o = json.loads(l)
            if o.get("status") == "ok":
                ok_done.add((o["file"], o["title"]))

    n_ok = n_fail = 0
    with open(out, "a", encoding="utf-8") as fo:   # 增量写，实时可见进度
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            pg = b.new_page()
            pg.set_default_timeout(30000)
            for fk, title in targets:
                if (fk, title) in ok_done:
                    n_ok += 1
                    print(f"  [skip-ok] {fk}/{title}", flush=True)
                    continue
                rec = {"file": fk, "title": title, "status": "fail", "baihua": "", "baihua_src": ""}
                # 候选查询：完整标题 -> 前3字 -> 前2字
                for q in [title, title[:3], title[:2]]:
                    try:
                        pg.goto("https://baike.baidu.com/item/" + q, wait_until="domcontentloaded", timeout=30000)
                        pg.wait_for_timeout(WAIT)
                        c = pg.content()
                        if "没有找到" in c or "抱歉，您要查看的" in c[:400] or "您访问的页面不存在" in c[:400]:
                            continue
                        bai = extract_baike(pg)
                        if is_baihua(bai):
                            rec = {"file": fk, "title": title, "status": "ok", "baihua": bai, "baihua_src": q}
                            break
                    except Exception as e:
                        continue
                if rec["status"] == "ok":
                    n_ok += 1
                    print(f"  [ok] {fk}/{title} <- 百度百科《{rec['baihua_src']}》(len={len(rec['baihua'])})", flush=True)
                else:
                    n_fail += 1
                    print(f"  [fail] {fk}/{title}", flush=True)
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fo.flush()
                pg.wait_for_timeout(int(SLEEP*1000))
            b.close()
    print(f"\n汇总: ok={n_ok} fail={n_fail} | 累计ok={len(ok_done)}", flush=True)

if __name__ == "__main__":
    main()
