# -*- coding: utf-8 -*-
"""dump 中国童话 doc[1]/doc[3] 的 b/p 元素顺序，确定切分规则。"""
from ebooklib import epub
from bs4 import BeautifulSoup

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

book = epub.read_epub(r'E:/BaiduNetdiskDownload/中国童话.epub')
docs = doc_items(book)

def dump(di, n=70):
    print('#' * 60)
    print('doc[%d] %s' % (di, docs[di].get_name()))
    s = soup_of(docs[di])
    seq = []
    for el in s.find_all(['b','p']):
        seq.append((el.name, el.get_text(strip=True)))
    for i,(tag,txt) in enumerate(seq[:n]):
        print(f'  {i:02d} <{tag}> {txt[:46]}')

dump(1)
dump(3)
