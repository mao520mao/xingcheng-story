# -*- coding: utf-8 -*-
"""深入检查 中国童话（无标题）与 格林童话（多doc聚合）的内部结构。"""
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
print('#' * 70)
print('中国童话 text00000.html 内部结构')
book = epub.read_epub(r'E:/BaiduNetdiskDownload/中国童话.epub')
docs = doc_items(book)
d0 = docs[0]
s = soup_of(d0)
print('  所有标题标签统计:')
from collections import Counter
c = Counter()
for tag in s.find_all(['h1','h2','h3','h4','h5','h6','p','div','span','b','strong']):
    c[tag.name] += 1
print('  ', dict(c))
# 打印前 3000 字纯文本，看故事如何分隔
text = s.get_text('\n', strip=True)
print('  --- 前 60 行 ---')
for line in text.split('\n')[:60]:
    print('   |', line[:80])
