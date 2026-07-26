# -*- coding: utf-8 -*-
import os, re
from ebooklib import epub
from bs4 import BeautifulSoup
sys_path = r'G:/gpt/星橙故事铺腾讯/app/build_extra_books.py'

# reuse functions by importing module
import importlib.util
spec = importlib.util.spec_from_file_location('beb', sys_path)
beb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(beb)

path = r'E:/BaiduNetdiskDownload/中国童话.epub'
docs = beb.docs_of(path)
print('doc count', len(docs))
# examine doc1 (first story doc)
for di in range(0, 2):
    html = docs[di]
    soup = BeautifulSoup(html, 'html.parser')
    print('==== DOC', di, '====')
    elems = soup.find_all(['b', 'p'])
    print('num b/p elems:', len(elems))
    n=0
    for el in elems:
        txt = beb.clean(el.get_text('', strip=True))
        if not txt: continue
        n+=1
        if n>40: break
        tag = el.name
        reason='?'
        if tag=='b':
            if beb.is_china_preview(txt): reason='PREVIEW'
            elif '给妈妈的话' in txt or '给爸爸的话' in txt: reason='TIP'
            elif beb.is_china_date_range(txt): reason='DATE'
            elif beb.is_china_brand(txt) or txt in beb.BOILER_TITLE: reason='BRAND'
            elif len(txt)>16: reason='TOOLONG(%d)'%len(txt)
            else: reason='TITLE?'
        else:
            reason='P'
        print('  [%s] %s | %s' % (tag, reason, txt[:34]))
