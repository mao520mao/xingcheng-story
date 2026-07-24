#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过古登堡搜索发现经典集的真实 eBook ID，并验证能切出真实故事。"""
import urllib.request, re, socket, time

socket.setdefaulttimeout(30)
H = {'User-Agent': 'Mozilla/5.0 (compatible; StoryBot/1.0)'}

def get(url):
    req = urllib.request.Request(url, headers=H)
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')

def search_ids(term, n=5):
    url = 'https://www.gutenberg.org/ebooks/search/?query=' + urllib.parse.quote(term)
    html = get(url)
    ids = re.findall(r'/ebooks/(\d+)', html)
    # 去重保序
    seen=set(); uniq=[]
    for i in ids:
        if i not in seen and i != '0000':
            seen.add(i); uniq.append(i)
    return uniq[:n]

def strip_gutenberg(text):
    m = re.search(r'\*\*\* START OF (THIS|THE) PROJECT GUTENBERG', text)
    if m: text = text[m.end():]
    m = re.search(r'\*\*\* END OF (THIS|THE) PROJECT GUTENBERG', text)
    if m: text = text[:m.start()]
    return text

def count_stories(body):
    lines = body.splitlines()
    cnt = 0
    for line in lines:
        s = line.strip()
        if s.isupper() and 3 <= len(s) <= 60 and not s.endswith('.') and not s.startswith('***'):
            su = s.upper()
            if any(k in su for k in ['NOTE','CONTENTS','PREFACE','INTRODUCTION','INDEX','ILLUSTRATION','BIBLIO','APPENDIX','GUTENBERG','TRANSLATOR','EDITOR','COPYRIGHT','LIST OF','PROJECT','EBOOK','START','END','BY ','VOLUME']):
                continue
            cnt += 1
    return cnt

import urllib.parse
TERMS = [
    'Andersen Fairy Tales',
    'Arabian Nights',
    'Lang Red Fairy Book',
    'Lang Blue Fairy Book',
    'Lang Yellow Fairy Book',
    'Lang Green Fairy Book',
    'Indian Fairy Tales',
    'The Jungle Book Kipling',
    'Fairy Tales every child',
    'Grimm Household Stories',
    'Hans Andersen',
    'Mother Goose',
]
for term in TERMS:
    try:
        ids = search_ids(term, 4)
    except Exception as e:
        print(f'[搜索失败] {term}: {e}')
        continue
    best = None
    for i in ids:
        try:
            txt = get(f'https://www.gutenberg.org/files/{i}/{i}-0.txt')
        except Exception:
            try:
                txt = get(f'https://www.gutenberg.org/files/{i}/{i}-8.txt')
            except Exception:
                continue
        body = strip_gutenberg(txt)
        c = count_stories(body)
        if c >= 5:
            best = (i, c)
            break
        time.sleep(0.5)
    if best:
        print(f'[命中] {term:28s} -> id={best[0]} 约 {best[1]} 篇')
    else:
        print(f'[未命中] {term:28s} -> 候选 {ids}')
    time.sleep(1)
