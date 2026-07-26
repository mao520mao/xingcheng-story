# -*- coding: utf-8 -*-
import os, re, sys
from ebooklib import epub
from bs4 import BeautifulSoup

BOOKS = {
    '成语故事': r'E:/BaiduNetdiskDownload/成语故事.epub',
    '历史传奇': r'E:/BaiduNetdiskDownload/历史传奇.epub',
    '意大利童话': r'E:/BaiduNetdiskDownload/意大利童话.epub',
    '格林童话（果麦版）': r'E:/BaiduNetdiskDownload/格林童话（果麦版）.epub',
    '中国童话': r'E:/BaiduNetdiskDownload/中国童话.epub',
}

def docs_of(path):
    book = epub.read_epub(path)
    out = []
    for item in book.get_items():
        mt = getattr(item, 'media_type', '') or ''
        if not mt.startswith('application/xhtml') and not mt.startswith('image/'):
            if 'html' not in (getattr(item,'file_name','') or ''):
                continue
        fn = item.get_name()
        if not (fn.lower().endswith('.xhtml') or fn.lower().endswith('.html')):
            continue
        try:
            html = item.get_content().decode('utf-8', 'ignore')
        except Exception:
            try:
                html = item.get_content().decode('gbk', 'ignore')
            except Exception:
                continue
        out.append((fn, html))
    return out

NUM_HEAD = re.compile(r'^\s*(\d{1,3})(?=[\u4e00-\u9fff])')  # number directly followed by chinese
DATE_LINE = re.compile(r'^\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*$')
BOILER = ('给妈妈的话', '给爸爸的话', '编辑室报告', '出版说明', '编者', '序', '前言', '后记', '目录')

def analyze(name, path):
    print('='*70)
    print('BOOK:', name, '->', path, 'exists=', os.path.exists(path))
    if not os.path.exists(path):
        return
    docs = docs_of(path)
    print('  doc count:', len(docs))
    numbered = []
    h_titles = []
    for fn, html in docs:
        soup = BeautifulSoup(html, 'html.parser')
        txt = soup.get_text('\n')
        lines = [l.strip() for l in txt.split('\n') if l.strip()]
        lead = lines[0] if lines else ''
        if NUM_HEAD.match(lead):
            numbered.append((fn, lead[:40]))
        hs = [h.get_text(strip=True) for h in soup.find_all(['h1','h2','h3','h4','h5','h6'])]
        if hs:
            h_titles.append((fn, hs[0][:40]))
        # china: count <b> titles
    if name == '中国童话':
        print('  --- China deep: per-doc <b> story-title candidates & date lines ---')
        total_b = 0
        total_date = 0
        for i,(fn,html) in enumerate(docs[:3]):
            soup = BeautifulSoup(html, 'html.parser')
            bs = [b.get_text(strip=True) for b in soup.find_all('b')]
            print('  doc', i, fn, 'num_b=', len(bs))
            # print first 25 b texts
            for t in bs[:25]:
                tag = 'DATE' if DATE_LINE.match(t) else ('BOILER' if any(t.startswith(x) for x in BOILER) else 'TITLE?')
                if tag!='BOILER':
                    print('     ', tag, repr(t[:30]))
            total_b += len(bs)
        print('  (only first 3 docs shown)')
    print('  sample numbered-title docs:', len(numbered))
    for fn,lead in numbered[:8]:
        print('     NUM', repr(lead))
    print('  sample h-title docs:', len(h_titles))
    for fn,ht in h_titles[:8]:
        print('     H  ', repr(ht))

for name, path in BOOKS.items():
    analyze(name, path)
