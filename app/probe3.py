#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查3：加重限流退避，用 categorymembers 发现真实分篇；验证大类存在性。"""
import urllib.request, urllib.parse, json, time, sys, re

API = "https://zh.wikisource.org/w/api.php"
UA = "Mozilla/5.0 (StarOrangeStoryBot/1.0)"
_last = 0.0
def _sleep(sec):
    global _last
    dt = sec - (time.time() - _last)
    if dt > 0: time.sleep(dt)
    _last = time.time()

def fetch_json(params, timeout=30, interval=1.5):
    params = dict(params); params['format']='json'
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for _ in range(5):
        _sleep(interval)
        try:
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("  [429 限流] 退避 20s", file=sys.stderr); time.sleep(20); continue
            print(f"  [HTTP {e.code}]", file=sys.stderr)
        except Exception as e:
            print(f"  [err] {e}", file=sys.stderr); time.sleep(3)
    return None

def category_members(cat, limit=500):
    out=[]
    cmcontinue=None
    while True:
        p={'action':'query','list':'categorymembers','cmtitle':cat,'cmlimit':min(limit,500)}
        if cmcontinue: p['cmcontinue']=cmcontinue
        j=fetch_json(p)
        if not j: break
        for m in j.get('query',{}).get('categorymembers',[]):
            out.append(m['title'])
        cmcontinue=j.get('continue',{}).get('cmcontinue')
        if not cmcontinue or len(out)>=limit: break
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
    cats = ['Category:伊索寓言','Category:安徒生童话','Category:格林童话','Category:一千零一夜',
            'Category:童话','Category:寓言','Category:民間故事','Category:王爾德童話','Category:希臘神話']
    for c in cats:
        mem = category_members(c, 60)
        print(f"\n[分类] {c}  → {len(mem)} 成员")
        for m in mem[:12]:
            print("   ", m)
    print("\n=== 直接验证几个真实分篇是否存在 ===")
    for t in ['伊索寓言/龜兔賽跑','伊索寓言/龟兔赛跑','安徒生童话/丑小鸭','格林童话/小紅帽','一千零一夜/阿拉丁']:
        wt=get_wikitext(t)
        print(f"  {'[存在]' if wt else '[缺失]'} {t}  ({0 if not wt else len(wt)} 字)")
