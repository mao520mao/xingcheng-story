# -*- coding: utf-8 -*-
"""侦察 5 本 EPUB 结构：文档列表、标题规律、每篇字数。"""
import os, sys
from ebooklib import epub
from bs4 import BeautifulSoup

BOOKS = {
    '中国童话': r'E:/BaiduNetdiskDownload/中国童话.epub',
    '成语故事': r'E:/BaiduNetdiskDownload/成语故事.epub',
    '格林童话': r'E:/BaiduNetdiskDownload/格林童话（果麦版）.epub',
    '历史传奇': r'E:/BaiduNetdiskDownload/历史传奇.epub',
    '意大利童话': r'E:/BaiduNetdiskDownload/意大利童话.epub',
}

def doc_items(book):
    items = []
    for it in book.get_items():
        mt = getattr(it, 'media_type', '') or ''
        name = it.get_name() or ''
        if 'html' in mt or name.endswith('.xhtml') or name.endswith('.html'):
            items.append(it)
    return items

for name, path in BOOKS.items():
    print('=' * 70)
    print('BOOK:', name)
    print('PATH:', path, '| EXISTS:', os.path.exists(path))
    if not os.path.exists(path):
        continue
    try:
        book = epub.read_epub(path)
    except Exception as e:
        print('  READ ERROR:', repr(e))
        continue
    docs = doc_items(book)
    print('  doc(html) count:', len(docs))
    # 统计标题
    rows = []
    for it in docs:
        fname = it.get_name()
        try:
            html = it.get_content().decode('utf-8', 'ignore')
        except Exception:
            html = it.get_content().decode('gbk', 'ignore')
        soup = BeautifulSoup(html, 'html.parser')
        h = soup.find(['h1', 'h2', 'h3'])
        title = h.get_text(strip=True) if h else '(no heading)'
        text = soup.get_text(' ', strip=True)
        rows.append((fname, len(text), title))
    # 展示前 20 个
    for i, (fname, ln, title) in enumerate(rows[:20]):
        print(f'   [{i:02d}] {fname[:50]:50s} len={ln:6d}  title={title[:30]}')
    if len(rows) > 20:
        print(f'   ... 共 {len(rows)} 个 doc，仅展示前 20')
    # 字数分布
    lens = [r[1] for r in rows]
    if lens:
        print(f'  字数: min={min(lens)} max={max(lens)} avg={sum(lens)//len(lens)}')
