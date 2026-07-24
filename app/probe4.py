#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查4：用 PrefixIndex(list=allpages&apprefix=) 发现真实分篇；测试整本书按 == 标题 == 切分。"""
import urllib.request, urllib.parse, json, time, sys, re

API = "https://zh.wikisource.org/w/api.php"
UA = "Mozilla/5.0 (StarOrangeStoryBot/1.0)"
_last=0.0
def _sleep(sec):
    global _last
    dt=sec-(time.time()-_last)
    if dt>0: time.sleep(dt)
    _last=time.time()

def fetch_json(params, interval=1.5):
    params=dict(params); params['format']='json'
    url=API+'?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url, headers={'User-Agent':UA})
    for _ in range(5):
        _sleep(interval)
        try:
            return json.loads(urllib.request.urlopen(req, timeout=30).read())
        except urllib.error.HTTPError as e:
            if e.code==429:
                print("  [429] 退避20s", file=sys.stderr); time.sleep(20); continue
            print(f"  [HTTP {e.code}]", file=sys.stderr)
        except Exception as e:
            print(f"  [err] {e}", file=sys.stderr); time.sleep(3)
    return None

def prefix_pages(prefix, limit=500):
    out=[]; apcontinue=None
    while True:
        p={'action':'query','list':'allpages','apnamespace':0,'apprefix':prefix,'aplimit':min(limit,500)}
        if apcontinue: p['apcontinue']=apcontinue
        j=fetch_json(p)
        if not j: break
        for pg in j.get('query',{}).get('allpages',[]):
            out.append(pg['title'])
        apcontinue=j.get('continue',{}).get('apcontinue')
        if not apcontinue or len(out)>=limit: break
    return out

def get_wikitext(title):
    j=fetch_json({'action':'query','prop':'revisions','titles':title,'rvprop':'content','rvslots':'main'})
    if not j: return None
    for pid,page in j.get('query',{}).get('pages',{}).items():
        if pid=='-1': return None
        if 'revisions' in page:
            return page['revisions'][0]['slots']['main']['*']
    return None

if __name__=='__main__':
    prefixes=['伊索寓言/','安徒生童话/','格林童话/','一千零一夜/','王尔德童话/','豪夫童话/',
              '拉封丹寓言/','克雷洛夫寓言/','列那狐的故事/','挪威童话/','希腊神话/','日本民间故事/',
              '印度寓言/','五卷书/','中国民间故事/','法国童话/','俄罗斯民间故事/','格林童话 ']
    print("=== PrefixIndex 发现真实分篇 ===")
    for pf in prefixes:
        pages=prefix_pages(pf, 300)
        print(f"\n[prefix] {pf!r} → {len(pages)} 页")
        for t in pages[:8]:
            print("   ", t)

    print("\n=== 整本书按 == 标题 == 切分测试 ===")
    for book in ['伊索寓言 (周作人)','伊索寓言演義','伊索寓言 (林紓)']:
        wt=get_wikitext(book)
        if not wt:
            print(f"  [缺失] {book}"); continue
        heads=re.findall(r'^==+\s*(.+?)\s*==+', wt, flags=re.M)
        print(f"  [存在] {book}  全文 {len(wt)} 字，== 级标题 {len(heads)} 个，示例: {heads[:6]}")
