# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import re, urllib.parse

def get_baike(pg, title):
    pg.goto("https://baike.baidu.com/item/" + urllib.parse.quote(title),
            wait_until="domcontentloaded", timeout=30000)
    pg.wait_for_timeout(2500)
    c = pg.content()
    txt = re.sub(r"<[^>]+>", "", c)
    txt = re.sub(r"\s+", " ", txt)
    if "没有找到" in txt or "抱歉" in txt[:200]:
        return None
    # 取摘要区: 百度百科摘要在 .lemma-summary 或前段
    i = txt.find(title[:2])
    return txt[i:i+200] if i >= 0 else txt[:200]

def main():
    names = ["张良","范蠡","宁封子","王子乔","东方朔","马师皇","吕尚","彭祖","介子推","江革","李广","黄庭坚","张载"]
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.set_default_timeout(30000)
        for t in names:
            try:
                r = get_baike(pg, t)
                print(f"{t:<6} ->", (r[:90] if r else "(无词条/未找到)"))
            except Exception as e:
                print(f"{t:<6} -> ERR: {str(e)[:40]}")
        b.close()

if __name__ == "__main__":
    main()
