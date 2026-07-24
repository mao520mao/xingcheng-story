#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查2：直接验证经典故事集索引页是否真实存在，并解析子故事链接；对比清洗方式。"""
import urllib.request, urllib.parse, json, time, sys, re

API = "https://zh.wikisource.org/w/api.php"
UA = "Mozilla/5.0 (StarOrangeStoryBot/1.0)"

def fetch_json(params, timeout=30):
    params = dict(params); params['format']='json'
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for _ in range(3):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        except Exception as e:
            print(f"  [retry] {e}", file=sys.stderr); time.sleep(2)
    return None

def get_wikitext(title):
    j = fetch_json({'action':'query','prop':'revisions','titles':title,'rvprop':'content','rvslots':'main'})
    if not j: return None
    for pid,page in j.get('query',{}).get('pages',{}).items():
        if 'revisions' in page:
            return page['revisions'][0]['slots']['main']['*']
    return None

def get_html(title):
    j = fetch_json({'action':'parse','page':title,'prop':'text','format':'json'})
    if not j: return None
    return j.get('parse',{}).get('text',{}).get('*')

INDEX_CANDIDATES = [
    '安徒生童话','格林童话','伊索寓言','一千零一夜','王尔德童话','豪夫童话',
    '拉封丹寓言','克雷洛夫寓言','列那狐的故事','挪威童话','希腊神话',
    '日本民间故事','印度寓言','五卷书','中国民间故事','法国童话','俄罗斯民间故事',
]

def extract_subpage_links(wikitext, base):
    """从索引页 wikitext 中提取形如 [[base/xxx|yyy]] 或 [[base/xxx]] 的子故事链接。"""
    links = []
    # 匹配 [[base/...|显示]] 或 [[base/...]]
    pat = re.compile(r'\[\[\s*(' + re.escape(base) + r'[^\]\|]+)(?:\|([^\]]+))?\s*\]\]')
    for m in pat.finditer(wikitext or ''):
        full = m.group(1).strip()
        disp = (m.group(2) or full.split('/')[-1]).strip()
        if full not in links:
            links.append(full)
    return links

if __name__ == '__main__':
    print("=== 验证索引页是否存在 + 解析子故事链接 ===")
    found_indexes = {}
    for idx in INDEX_CANDIDATES:
        wt = get_wikitext(idx)
        if wt is None:
            print(f"[缺失] {idx}")
            continue
        # 取 base 为该索引页标题
        subs = extract_subpage_links(wt, idx)
        # 若索引页本身没用 base/ 形式，尝试找任意 [[.../...]] 子页
        if not subs:
            subs = extract_subpage_links(wt, '')
            subs = [s for s in subs if '/' in s][:30]
        print(f"[存在] {idx}  →  子故事链接 {len(subs)} 条，示例: {subs[:6]}")
        found_indexes[idx] = subs[:60]

    print("\n=== 选一个真实子故事，对比 wikitext vs HTML 清洗 ===")
    # 尝试常见子故事
    probes = [
        '安徒生童话/丑小鸭','安徒生童话/賣火柴的小女孩','格林童话/小紅帽','伊索寓言/龜兔賽跑',
        '一千零一夜/阿拉丁和神灯','王尔德童话/快樂王子',
    ]
    for p in probes:
        wt = get_wikitext(p)
        if wt:
            print(f"\n##### 真实页：{p} （wikitext {len(wt)} 字）")
            print("--- wikitext 片段 ---")
            print(wt[:900])
            html = get_html(p)
            if html:
                print("--- html 长度:", len(html), "---")
            break
