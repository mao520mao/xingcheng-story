#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验候选古登堡 ID 是否真的是对应经典集（按文件头 Title 元数据）。"""
import urllib.request, re, socket, time, sys
socket.setdefaulttimeout(30)
H = {'User-Agent': 'Mozilla/5.0 (compatible; StoryBot/1.0)'}

CANDIDATES = [
    ('Andersen Fairy Tales', 1597),
    ('Arabian Nights', 34206),
    ('Lang Yellow Fairy Book', 503),
    ('Lang Green Fairy Book', 27826),
    ('Indian Fairy Tales', 7128),
    ('The Jungle Book', 236),
    ('Fairy Tales Every Child', 16537),
    ('Grimm Household Stories', 5314),
    ('Lang Red Fairy Book', 26670),
    ('Lang Blue Fairy Book', 2650),
    ('The Pink Fairy Book', 28571),
    ('The Grey Fairy Book', 28481),
    ('The Crimson Fairy Book', 28385),
    ('The Brown Fairy Book', 28215),
    ('The Orange Fairy Book', 28113),
    ('The Lilac Fairy Book', 28015),
]

def get(url):
    req = urllib.request.Request(url, headers=H)
    return urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'ignore')

def meta_title(txt):
    m = re.search(r'Title:\s*(.+)', txt[:4000])
    return m.group(1).strip() if m else '(无Title)'

def count_stories(body):
    cnt = 0
    for line in body.splitlines():
        s = line.strip()
        if not (s.isupper() and 3 <= len(s) <= 60 and not s.endswith('.') and not s.startswith('***')):
            continue
        su = s.upper()
        if any(k in su for k in ['NOTE','CONTENTS','PREFACE','INTRODUCTION','INDEX','ILLUSTRATION','BIBLIO','APPENDIX','GUTENBERG','TRANSLATOR','EDITOR','COPYRIGHT','LIST OF','PROJECT','EBOOK','START','END','BY ','VOLUME']):
            continue
        cnt += 1
    return cnt

for name, idn in CANDIDATES:
    try:
        txt = get(f'https://www.gutenberg.org/files/{idn}/{idn}-0.txt')
    except Exception as e:
        try:
            txt = get(f'https://www.gutenberg.org/files/{idn}/{idn}-8.txt')
        except Exception as e2:
            print(f'[失败] {name:24s} id={idn} -> {e2}')
            time.sleep(2); continue
    title = meta_title(txt)
    body = txt
    m = re.search(r'\*\*\* START OF', body)
    if m: body = body[m.end():]
    m = re.search(r'\*\*\* END OF', body)
    if m: body = body[:m.start()]
    c = count_stories(body)
    # 判定标题是否命中期望关键词
    key = name.lower().replace('fairy book','').replace('fairy tales','').replace('the','').strip()
    hit = key in title.lower() or name.split()[0].lower() in title.lower()
    flag = '✓' if hit else '✗(疑似不对)'
    print(f'[{flag}] {name:24s} id={idn:6d} 真实书名="{title}" 约 {c} 篇')
    time.sleep(2)
