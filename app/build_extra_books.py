# -*- coding: utf-8 -*-
"""
V18: 抽取 5 本新书 (中国童话/成语故事/格林童话(果麦版)/历史传奇/意大利童话)
并合并 V17 已有的 175 篇(标签规范化为 安徒生/王尔德)。
输出 app/js/stories_data.js -> window.STORY_LIBRARY_EXT
偏好模型: 偏好名 == 故事标签 == 书名; 选中即开启对应书籍; 支持多选。
"""
import os, re, json
from ebooklib import epub
from bs4 import BeautifulSoup

APP = r'G:/gpt/星橙故事铺腾讯/app'
DATA_JS = os.path.join(APP, 'js', 'stories_data.js')

BOOKS = {
    '中国童话':            {'path': r'E:/BaiduNetdiskDownload/中国童话.epub',            'tag': '中国童话',            'culture': '中国', 'country': '中国', 'author': '汉声杂志社',            'prefix': 'china', 'strategy': 'china'},
    '成语故事':            {'path': r'E:/BaiduNetdiskDownload/成语故事.epub',            'tag': '成语故事',            'culture': '中国', 'country': '中国', 'author': '',                       'prefix': 'chengyu', 'strategy': 'one_doc'},
    '格林童话（果麦版）':  {'path': r'E:/BaiduNetdiskDownload/格林童话（果麦版）.epub',  'tag': '格林童话（果麦版）',  'culture': '德国', 'country': '德国', 'author': '雅各布·格林、威廉·格林',  'prefix': 'grimm', 'strategy': 'numbered'},
    '历史传奇':            {'path': r'E:/BaiduNetdiskDownload/历史传奇.epub',            'tag': '历史传奇',            'culture': '中国', 'country': '中国', 'author': '',                       'prefix': 'lishi', 'strategy': 'one_doc'},
    '意大利童话':          {'path': r'E:/BaiduNetdiskDownload/意大利童话.epub',          'tag': '意大利童话',          'culture': '意大利', 'country': '意大利', 'author': '伊塔洛·卡尔维诺',        'prefix': 'italy', 'strategy': 'one_doc'},
}

BOILER_TITLE = {'目录', '目录contents', 'contents', '序', '序言', '制作说明', '版权信息',
                '编者', '前言', '后记', '出版说明', '作者为中译本所题的几句话', 'landmarks',
                '版本说明', '译者序'}
BOILER_SUB = ('cip', '图书在版编目', '译后', 'folk tales', 'selected and retold', 'calvino',
              'copyright', '版权所有', '出版发行', '责任编辑', '书名', 'isbn')
NUM_HEAD = re.compile(r'^\s*\d{1,3}(?=[\u4e00-\u9fff])')
GRIMM_NUM = re.compile(r'^\s*0?\d{1,3}[\s、.．、]*')
# 日期区间(支持中文/阿拉伯数字): "十二月三十日～一月十日的故事"
DATE_RANGE = re.compile(r'[\u4e00-\u9fff\d]{1,3}\s*月\s*[\u4e00-\u9fff\d]{1,3}\s*日[\s\S]{0,12}的故事')
# 中国童话 品牌/样板 精确匹配
CHINA_BRAND_EXACT = {'春', '夏', '秋', '冬', '总目录', '中国童话', '最美最美的中国童话',
                     '汉声杂志社编写·绘图', '江苏美术出版社', '原书书名：汉声《中国童话》'}
# 中国童话 品牌/样板 子串匹配
CHINA_BRAND_SUB = ('小读客', '最美最美的', '汉声', '江苏美术', '原书书名', '版权', '印刷',
                   '用彩笔', '让汉声', '成为十几亿', '农历', '编写·绘图', '故事馆', '授权',
                   '读客', '孩童', '出版', '想听', '继续', '等精彩故事', '打开《')

def clean(s):
    s = re.sub(r'[\u3000\xa0]+', ' ', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n{2,}', '\n', s)
    return s.strip()

def docs_of(path):
    book = epub.read_epub(path)
    out = []
    for item in book.get_items():
        fn = (getattr(item, 'file_name', '') or '').lower()
        if not (fn.endswith('.xhtml') or fn.endswith('.html')):
            continue
        try:
            html = item.get_content().decode('utf-8', 'ignore')
        except Exception:
            try:
                html = item.get_content().decode('gbk', 'ignore')
            except Exception:
                continue
        out.append(html)
    return out

def paras_of(html):
    soup = BeautifulSoup(html, 'html.parser')
    blocks = []
    for el in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b', 'div']):
        t = el.get_text('', strip=True)
        if t:
            blocks.append(t)
    return blocks

def title_of(html):
    soup = BeautifulSoup(html, 'html.parser')
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        t = h.get_text(strip=True)
        if t:
            return t
    # fallback: first non-empty paragraph
    for p in soup.find_all('p'):
        t = p.get_text(strip=True)
        if t:
            return t
    return ''

def build_story(sid, title, content, meta):
    content = clean(content)
    if not content:
        return None
    dur = max(2, (len(content) + 299) // 300)
    first_para = content.split('\n')[0]
    summary = (first_para[:100] + '…') if len(first_para) > 100 else first_para
    return {
        'id': sid,
        'title': title,
        'summary': summary,
        'content': content,
        'tags': [meta['tag']],
        'country': meta['country'],
        'culture': meta['culture'],
        'author': meta['author'],
        'collection': meta['tag'],
        'source': os.path.basename(meta['path']),
        'popularity': 4,
        'duration': dur,
        'ageMin': 8,
        'ageMax': 13,
        'safetyChecked': True,
        'version': '1.0.0',
    }

def slug(t):
    t = re.sub(r'[^\w\u4e00-\u9fff]+', '_', t)
    return t.strip('_')[:24] or 'x'

def extract_one_doc(book, meta):
    """1 doc = 1 story (成语/历史/意大利). Returns list with 0 or 1 story."""
    res = []
    html = book
    title = title_of(html)
    if not title:
        return res
    t = title.strip()
    tl = t.lower()
    # 样板标题(精确或子串)
    if tl in BOILER_TITLE or any(k in tl for k in BOILER_SUB) or len(clean(t)) < 2:
        return res
    # 英文标题页 / 拉丁字母占多数 -> 跳过
    if re.search(r'[a-zA-Z]{5,}', t) and len(re.findall(r'[a-zA-Z]', t)) > len(t) * 0.5:
        return res
    soup = BeautifulSoup(html, 'html.parser')
    # content = all paragraph text minus title
    paras = [p.get_text('', strip=True) for p in soup.find_all('p')]
    content = '\n'.join(p for p in paras if p and p != t)
    if len(content) < 120:
        return res
    sid = '%s_%02d_%s' % (meta['prefix'], extract_one_doc.counter[meta['prefix']] + 1, slug(t))
    extract_one_doc.counter[meta['prefix']] += 1
    s = build_story(sid, t, content, meta)
    if s:
        res.append(s)
    return res

extract_one_doc.counter = {}

def extract_numbered(docs, meta):
    """格林童话: 编号标题文档开始新故事, 后续无标题文档为续篇。"""
    stories = []
    cur = None
    idx = 0
    for html in docs:
        title = title_of(html)
        is_head = bool(title and GRIMM_NUM.match(title))
        if is_head:
            if cur:
                stories.append(cur)
            raw = title.strip()
            name = GRIMM_NUM.sub('', raw).strip()
            idx += 1
            sid = '%s_%03d_%s' % (meta['prefix'], idx, slug(name))
            cur = {'sid': sid, 'title': name, 'parts': []}
        soup = BeautifulSoup(html, 'html.parser')
        paras = [p.get_text('', strip=True) for p in soup.find_all('p')]
        content = '\n'.join(p for p in paras if p)
        if cur is not None:
            cur['parts'].append(content)
    if cur:
        stories.append(cur)
    out = []
    for st in stories:
        full = clean('\n'.join(st['parts']))
        if len(full) < 120:
            continue
        s = build_story(st['sid'], st['title'], full, meta)
        if s:
            out.append(s)
    return out

def is_china_brand(t):
    if t in CHINA_BRAND_EXACT:
        return True
    return any(p in t for p in CHINA_BRAND_SUB)

def is_china_date_range(t):
    txt = t
    tt = t.rstrip()
    # 区间页眉: "X月X日～Y月Z日的故事" / "十二月三十日～一月十日的故事"
    if ('～' in txt or '~' in txt) and '日' in txt and '故事' in txt:
        return True
    # 单日分节: "...月...日...的故事"
    if tt.endswith('的故事') and '月' in txt and '日' in txt:
        return True
    return bool(DATE_RANGE.search(txt))

def is_china_preview(t):
    return any(m in t for m in ('想听', '继续──', '明天的故事', '打开《')) or '等精彩故事' in t

def extract_china(docs, meta):
    """中国童话: 无 h 标题。布局为「标题 <b> 标注其后的内容块」, 且每篇文档首个故事常无标题。
    规则:
      - <b> 真实故事标题 -> 标注接下来的一段 <p> 内容 (title 标记下一个块)
      - 跳过 品牌/日期区间/家长话(给妈妈的话)/下月预告 等样板
      - 家长话区块(标题+其 <p> 内容)整段忽略; 遇到下一个真实标题时退出 tip 态
      - 文档开头无标题的内容块 -> 用顺序编号(第N则)作标题 (避免丢失)
    """
    stories = []
    gen = [0]
    for html in docs:
        soup = BeautifulSoup(html, 'html.parser')
        elems = soup.find_all(['b', 'p'])
        cur = None
        title_for_next = None
        in_tip = False
        in_preview = False
        for el in elems:
            txt = clean(el.get_text('', strip=True))
            if not txt:
                continue
            if el.name == 'b':
                if is_china_preview(txt):
                    in_preview = True
                    in_tip = False
                    if cur:
                        stories.append(cur); cur = None
                    title_for_next = None
                    continue
                if in_preview:
                    continue
                if '给妈妈的话' in txt or '给爸爸的话' in txt or txt.startswith('给妈妈') or txt.startswith('给爸爸'):
                    in_tip = True
                    if cur:
                        stories.append(cur); cur = None
                    title_for_next = None
                    continue
                if in_tip:
                    # 遇到下一个真实标题 -> 退出 tip 态, 继续按标题处理
                    in_tip = False
                if is_china_date_range(txt):
                    # 日期区间页眉: 仅作分节, 不作为故事, 也不用于命名
                    if cur:
                        stories.append(cur); cur = None
                    title_for_next = None
                    continue
                if is_china_brand(txt) or txt in BOILER_TITLE:
                    continue
                if len(txt) > 16:
                    continue
                # 真实故事标题: 标注接下来的内容块
                if cur:
                    stories.append(cur)
                cur = None
                title_for_next = txt
                continue
            else:  # <p> 正文
                if in_tip or in_preview:
                    continue
                if cur is None:
                    if title_for_next:
                        t = title_for_next
                        title_for_next = None
                    else:
                        gen[0] += 1
                        t = ('第%d则' % gen[0])
                    idx = len(stories) + 1
                    sid = '%s_%03d_%s' % (meta['prefix'], idx, slug(t) or ('g%d' % gen[0]))
                    cur = {'sid': sid, 'title': t, 'parts': []}
                cur['parts'].append(txt)
        if cur:
            stories.append(cur)
    out = []
    for st in stories:
        full = clean('\n'.join(st['parts']))
        if len(full) < 260:   # 中国童话: 过滤过短碎片(被 bold 子标题误切的)
            continue
        s = build_story(st['sid'], st['title'], full, meta)
        if s:
            out.append(s)
    return out

def load_existing():
    with open(DATA_JS, 'r', encoding='utf-8') as f:
        txt = f.read()
    i = txt.index('[')
    j = txt.rindex(']')
    arr = json.loads(txt[i:j+1])
    # 标签规范化为短书名 (与 V17 偏好名一致)
    for s in arr:
        newtags = []
        for t in s.get('tags', []):
            if t == '安徒生童话':
                newtags.append('安徒生')
            elif t == '王尔德童话':
                newtags.append('王尔德')
            else:
                newtags.append(t)
        s['tags'] = newtags
        s['collection'] = '安徒生' if '安徒生' in newtags else ('王尔德' if '王尔德' in newtags else s.get('collection', ''))
    return arr

def main():
    existing = load_existing()
    print('现有库(标签已规范化):', len(existing))
    from collections import Counter
    print('  标签分布:', dict(Counter(t for s in existing for t in s['tags'])))

    all_new = []
    report = []
    for name, meta in BOOKS.items():
        if not os.path.exists(meta['path']):
            print('!! 缺失:', meta['path'])
            report.append((name, 0, 'MISSING'))
            continue
        extract_one_doc.counter[meta['prefix']] = 0
        docs = docs_of(meta['path'])
        if meta['strategy'] == 'one_doc':
            got = []
            for h in docs:
                got += extract_one_doc(h, meta)
        elif meta['strategy'] == 'numbered':
            got = extract_numbered(docs, meta)
        elif meta['strategy'] == 'china':
            got = extract_china(docs, meta)
        else:
            got = []
        all_new += got
        report.append((name, len(got), meta['path']))
        print('抽取 %s: %d 篇' % (name, len(got)))

    merged = existing + all_new
    tagcnt = Counter(t for s in merged for t in s['tags'])
    print('合并后总篇数:', len(merged))
    print('合并后标签分布:', dict(tagcnt))
    miss = [s['id'] for s in merged if not s.get('content') or not s.get('title') or not s.get('duration')]
    print('字段缺失:', len(miss))
    # 写出
    body = 'window.STORY_LIBRARY_EXT = ' + json.dumps(merged, ensure_ascii=False, indent=0) + ';\n'
    with open(DATA_JS, 'w', encoding='utf-8') as f:
        f.write(body)
    print('已写出', DATA_JS, '大小', os.path.getsize(DATA_JS))
    # 报告
    print('\n--- 各书抽取报告 ---')
    for r in report:
        print(r)

if __name__ == '__main__':
    main()
