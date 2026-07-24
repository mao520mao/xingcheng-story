# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import re, urllib.parse

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.set_default_timeout(30000)

        # 1) 古诗文网 搜索 宁封子
        print("=== 古诗文网 搜 宁封子 ===")
        try:
            pg.goto("https://so.gushiwen.cn/search.aspx?value=" + urllib.parse.quote("宁封子"),
                    wait_until="networkidle", timeout=30000)
            html = pg.content()
            print("页面长度:", len(html))
            links = re.findall(r"/shiwenv_[a-z0-9]+\.aspx", html)
            print("候选链接:", links[:3])
            if links:
                pg.goto("https://so.gushiwen.cn" + links[0], wait_until="networkidle", timeout=30000)
                ph = pg.content()
                # 古诗文网译文区：正文在 .contyishang 内，找“译文”后文本
                m = re.search(r"译文[^\u4e00-\u9fff]{0,4}[:：]?\s*(.{20,600}?)</", ph)
                if not m:
                    m = re.search(r"翻译[^\u4e00-\u9fff]{0,4}[:：]?\s*(.{20,600}?)</", ph)
                print("译文:", (m.group(1)[:200] if m else "未定位译文区"))
                # 也看一下页面里是否含“译文”二字
                print("页面含'译文':", "译文" in ph)
        except Exception as e:
            print("古诗文网 ERR:", e)

        # 2) 百度百科 张良
        print("\n=== 百度百科 张良 ===")
        try:
            pg.goto("https://baike.baidu.com/item/" + urllib.parse.quote("张良"),
                    wait_until="networkidle", timeout=30000)
            txt = re.sub(r"<[^>]+>", "", pg.content())
            txt = re.sub(r"\s+", " ", txt)
            i = txt.find("张良")
            print("摘要:", txt[i:i+150] if i >= 0 else "(无)")
            print("页面长度:", len(pg.content()))
        except Exception as e:
            print("百度百科 ERR:", e)

        b.close()

if __name__ == "__main__":
    main()
