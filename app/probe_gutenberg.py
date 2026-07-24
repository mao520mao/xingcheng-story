#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证古登堡真实英文经典童话能否抓取并切成单篇。"""
import urllib.request, re, sys, socket, time

socket.setdefaulttimeout(30)
H = {'User-Agent': 'Mozilla/5.0 (compatible; StoryBot/1.0)'}

# 候选真实公版经典集（古登堡 eBook ID，凭已知书目，内容以抓取后判定）
CANDIDATES = [
    (2591,  'Grimm',     'Grimm\'s Fairy Tales'),
    (902,   'Wilde',     'The Happy Prince and Other Tales'),
    (11339, 'Aesop',     'Aesop\'s Fables'),
    (2701,  'Andersen',  'Andersen\'s Fairy Tales'),
    (5660,  'Arabian',   'The Arabian Nights (Burton)'),
]

def fetch(idn):
    for suf in ('-8', '-0'):
        url = f'https://www.gutenberg.org/files/{idn}/{idn}{suf}.txt'
        try:
            req = urllib.request.Request(url, headers=H)
            data = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
            return url, data
        except Exception as e:
            last = f'{type(e).__name__}:{str(e)[:50]}'
    return None, last

def detect_stories(text):
    """粗略探测单篇标题行：全大写 / 标题大小写短行 / 数字编号。"""
    lines = [l.rstrip() for l in text.splitlines()]
    heads = []
    for l in lines:
        s = l.strip()
        if not s or len(s) > 80:
            continue
        if re.match(r'^(CHAPTER|CONTENTS|PROJECT GUTENBERG|PREFACE|INTRODUCTION)', s, re.I):
            continue
        # 全大写标题
        if s.isupper() and len(s) > 3:
            heads.append(s)
        # "I. The ...", "1. The ..." 编号
        elif re.match(r'^[IVXLC\d]+\.\s+[A-Z]', s):
            heads.append(s)
        # 标题大小写、无句号的短行
        elif re.match(r'^[A-Z][A-Za-z\' ]{4,60}$', s) and not s.endswith('.'):
            heads.append(s)
    # 去重保序
    seen=set(); uniq=[]
    for h in heads:
        if h not in seen:
            seen.add(h); uniq.append(h)
    return uniq[:25]

for idn, author, name in CANDIDATES:
    url, res = fetch(idn)
    if url is None:
        print(f'[缺失] {name} (id={idn}) -> {res}')
        continue
    print(f'\n=== [{author}] {name} (id={idn}) ===')
    print(f'url: {url}')
    print(f'chars: {len(res)}')
    # 找正文起点（跳过 Gutenberg 头）
    m = re.search(r'\*\*\* START OF (THIS|THE) PROJECT GUTENBERG', res)
    body = res[m.end():] if m else res
    mb = re.search(r'\*\*\* END OF (THIS|THE) PROJECT GUTENBERG', body)
    if mb:
        body = body[:mb.start()]
    print(f'正文 chars: {len(body)}')
    heads = detect_stories(body)
    print(f'探测到的可能单篇标题(前15): {heads[:15]}')
    time.sleep(1)
