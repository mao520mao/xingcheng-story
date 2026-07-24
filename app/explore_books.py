# -*- coding: utf-8 -*-
import sys, os, re
from ebooklib import epub
from bs4 import BeautifulSoup

VENV = "c:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe"

def docs_of(path):
    book = epub.read_epub(path)
    items = []
    for item in book.get_items():
        mt = getattr(item, 'media_type', '') or ''
        name = item.get_name().lower()
        if mt in ('application/xhtml+xml','text/html','application/xhtml') or name.endswith(('.xhtml','.html','.htm')):
            items.append(item)
    return book, items

def headings(soup):
    hs = []
    for tag in soup.find_all(['h1','h2','h3','h4','h5','h6']):
        t = tag.get_text(strip=True)
        if t:
            hs.append((tag.name, t))
    return hs

def text_len(soup):
    return len(soup.get_text(strip=True))

# ---------- EPUB (安徒生) ----------
epub_path = "G:/gpt/星橙故事铺腾讯/新故事/安徒生童话）.epub"
print("="*60)
print("EPUB:", epub_path)
book, items = docs_of(epub_path)
print("文档文件数:", len(items))
total_chars = 0
for it in items:
    soup = BeautifulSoup(it.get_content(), "html.parser")
    hs = headings(soup)
    tl = text_len(soup)
    total_chars += tl
    fname = it.get_name()
    print(f"\n[{fname}] 字数={tl} 标题数={len(hs)}")
    for name, t in hs[:12]:
        print(f"   {name}: {t}")
print(f"\nEPUB 总字数(粗估): {total_chars}")

# ---------- MOBI (王尔德) ----------
mobi_path = "G:/gpt/星橙故事铺腾讯/新故事/王尔德童话.mobi"
print("\n" + "="*60)
print("MOBI:", mobi_path)
import mobi
tempdir, html_tmp = mobi.extract(mobi_path)
print("mobi 提取临时 html:", html_tmp)
with open(html_tmp, encoding="utf-8", errors="ignore") as f:
    soup = BeautifulSoup(f.read(), "html.parser")
hs = headings(soup)
print("MOBI 单文件 标题数:", len(hs))
tl = text_len(soup)
print("MOBI 单文件 字数(粗估):", tl)
for name, t in hs[:60]:
    print(f"   {name}: {t}")
