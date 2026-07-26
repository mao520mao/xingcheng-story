# -*- coding: utf-8 -*-
"""检查 中国童话 的 <b> 标题与日期切分规律；并确认 格林童话 编号标题聚合。"""
from ebooklib import epub
from bs4 import BeautifulSoup
import re

def doc_items(book):
    out = []
    for it in book.get_items():
        mt = getattr(it, 'media_type', '') or ''
        name = it.get_name() or ''
        if 'html' in mt or name.endswith('.xhtml') or name.endswith('.html'):
            out.append(it)
    return out

def soup_of(it):
    try:
        html = it.get_content().decode('utf-8', 'ignore')
    except Exception:
        html = it.get_content().decode('gbk', 'ignore')
    return BeautifulSoup(html, 'html.parser')

# ---------- 中国童话 ----------
print('=' * 70)
print('中国童话：各 doc 的 <b> 标题样本')
book = epub.read_epub(r'E:/BaiduNetdiskDownload/中国童话.epub')
docs = doc_items(book)
for di, it in enumerate(docs[:4]):
    s = soup_of(it)
    bs = [b.get_text(strip=True) for b in s.find_all('b')]
    print(f'-- doc[{di}] {it.get_name()}  b_count={len(bs)}')
    for t in bs[:25]:
        print('    B:', t[:50])

# 找日期模式
print()
print('中国童话 text00001 中匹配 日期/标题 的行样本：')
s = soup_of(docs[1])
paras = [p.get_text(strip=True) for p in s.find_all('p')]
date_re = re.compile(r'^\s*([一二三四五六七八九十]+月[初十一二三四五六七八九十]+[日号]?|正[月日])')
hits = [p for p in paras if date_re.match(p)]
print('  日期匹配行数:', len(hits))
for h in hits[:20]:
    print('    D:', h[:50])

# ---------- 格林童话 编号标题聚合检查 ----------
print()
print('=' * 70)
print('格林童话：扫描所有 doc 的标题，找编号故事标题')
book2 = epub.read_epub(r'E:/BaiduNetdiskDownload/格林童话（果麦版）.epub')
docs2 = doc_items(book2)
num_re = re.compile(r'^\s*0*(\d{1,3})[\.、\s、]')
groups = []
cur = None
for it in docs2:
    s = soup_of(it)
    h = s.find(['h1','h2','h3'])
    title = h.get_text(strip=True) if h else ''
    text = s.get_text(' ', strip=True)
    if num_re.match(title):
        m = num_re.match(title)
        n = int(m.group(1))
        if cur is not None:
            groups.append(cur)
        cur = {'n': n, 'title': title, 'docs': [it.get_name()], 'len': len(text)}
    else:
        if cur is not None:
            cur['docs'].append(it.get_name())
            cur['len'] += len(text)
if cur: groups.append(cur)
print('  编号故事组数:', len(groups))
for g in groups[:10]:
    print(f"   #{g['n']:02d} {g['title'][:24]:24s} docs={len(g['docs'])} len={g['len']}")
if len(groups) > 10:
    print('   ... 末 5 组:')
    for g in groups[-5:]:
        print(f"   #{g['n']:02d} {g['title'][:24]:24s} docs={len(g['docs'])} len={g['len']}")
