#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查维基文库：确认能拿到真实故事标题列表 + 真实正文，并观察文本格式。"""
import urllib.request, urllib.parse, json, time, sys

API = "https://zh.wikisource.org/w/api.php"
UA = "Mozilla/5.0 (StarOrangeStoryBot/1.0; contact: local)"

def fetch_json(params, timeout=30):
    params = dict(params)
    params['format'] = 'json'
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for attempt in range(3):
        try:
            data = urllib.request.urlopen(req, timeout=timeout).read()
            return json.loads(data)
        except Exception as e:
            print(f"  [retry {attempt+1}] {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(2)
    return None

def search_titles(q, limit=10):
    j = fetch_json({'action':'query','list':'search','srsearch':q,'srlimit':limit})
    if not j: return []
    return [r['title'] for r in j.get('query',{}).get('search',[])]

def category_members(cat, limit=50):
    j = fetch_json({'action':'query','list':'categorymembers','cmtitle':cat,'cmlimit':limit})
    if not j: return []
    return [m['title'] for m in j.get('query',{}).get('categorymembers',[])]

def get_wikitext(title):
    j = fetch_json({'action':'query','prop':'revisions','titles':title,'rvprop':'content','rvslots':'main','rvlimit':1})
    if not j: return None
    pages = j.get('query',{}).get('pages',{})
    for pid, page in pages.items():
        revs = page.get('revisions',[])
        if revs:
            slot = revs[0].get('slots',{}).get('main',{})
            return slot.get('*')
    return None

if __name__ == '__main__':
    print("=== 探查：搜索真实故事集 ===")
    for q in ['安徒生童话','格林童话','伊索寓言','一千零一夜']:
        titles = search_titles(q, 5)
        print(f"\n搜索『{q}』→")
        for t in titles:
            print("   ", t)

    print("\n=== 探查：分类成员（若有分类页）===")
    for cat in ['Category:安徒生童话','Category:格林童话','Category:伊索寓言']:
        mem = category_members(cat, 8)
        print(f"\n分类『{cat}』→")
        for m in mem:
            print("   ", m)

    print("\n=== 探查：抓取一篇真实正文样例 ===")
    # 用搜索结果里像故事页的标题试抓
    cand = search_titles('丑小鸭', 3) + search_titles('卖火柴的小女孩', 3)
    for t in cand:
        print(f"\n--- 试抓：{t} ---")
        wt = get_wikitext(t)
        if wt:
            print("wikitext 前 1200 字：")
            print(wt[:1200])
            break
        else:
            print("  无 wikitext")
