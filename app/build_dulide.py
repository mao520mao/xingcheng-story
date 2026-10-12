# -*- coding: utf-8 -*-
"""
从《怪医杜立德（果麦经典）》EPUB 直提真实正文，追加进 stories_data.js。
长篇连载：19 章，按原书顺序排列 → 进「长篇馆」。

结构：calibre 转换版，每章跨 2 个 HTML 文件
  - 章首文件：<h1 ... title="CHAPTER 01 泥塘镇">  + 若干 <p>
  - 续页文件：只有 <p>
噪声：目录页 / Landmarks / 版权页(CIP) / 书尾「扫一扫」广告 / 出品人员名单
"""
import zipfile, re, html, json, os, shutil

SRC = 'D:/admin/Downloads/4701-怪医杜立德（果麦经典）/怪医杜立德（果麦经典）.epub'
LIB = 'G:/gpt/星橙故事铺腾讯/app/js/stories_data.js'
BOOK = '怪医杜立德'
ID_PREFIX = 'ddl'
AUTHOR = '休·洛夫廷'
COUNTRY = '美国'
SOURCE = '怪医杜立德（果麦经典）.epub'

# 整文件级别的噪声（命中即整页丢弃）
FILE_NOISE = [
    '图书在版编目', 'ISBN', '目录 Contents', 'Landmarks', 'Table of Contents',
    '扫一扫', '产品经理', '装帧设计', '插画绘制', '技术编辑',
    'ePUBw', 'z-library', '1lib',
]
# 段落级别的噪声（命中即丢弃该段）
P_NOISE = ['扫一扫', 'z-library', 'ePUBw', 'www.', 'http://', 'http://']


def clean(t):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', t))).strip()


def parse():
    z = zipfile.ZipFile(SRC)
    files = sorted(
        [n for n in z.namelist() if re.search(r'part\d+\.html$', n)],
        key=lambda x: int(re.search(r'(\d+)', x.split('/')[-1]).group(1))
    )
    chapters = []          # [{'no':int,'title':str,'paras':[str]}]
    cur = None
    for f in files:
        raw = z.read(f).decode('utf-8', 'replace')

        # 章节起始：<h1 ... title="CHAPTER 01 泥塘镇">
        m = re.search(r'<h1[^>]*title="([^"]*)"', raw)
        if m:
            t = clean(m.group(1))
            m2 = re.match(r'CHAPTER\s*(\d+)\s*(.*)', t, re.I)
            if m2:
                no = int(m2.group(1))
                name = m2.group(2).strip() or ('第%d章' % no)
                cur = {'no': no, 'title': name, 'paras': []}
                chapters.append(cur)

        # 噪声页（还没开章的目录/版权页自然无 cur，直接跳过）
        page_txt = clean(raw)
        if any(k in page_txt for k in FILE_NOISE):
            continue
        if cur is None:
            continue
        if len(page_txt) < 60:      # 空页/占位页
            continue

        # 正文段落
        for p in re.findall(r'<p[^>]*>(.*?)</p>', raw, re.S):
            t = clean(p)
            if not t:
                continue
            if any(k in t for k in P_NOISE):
                continue
            cur['paras'].append(t)
    return chapters


def build(chapters):
    objs = []
    for c in chapters:
        content = '\n'.join(c['paras']).strip()
        if len(content) < 120:
            continue
        first = c['paras'][0]
        summary = first if len(first) <= 80 else first[:78] + '…'
        objs.append({
            'id': '%s_%03d_%s' % (ID_PREFIX, c['no'], c['title']),
            'title': c['title'],
            'summary': summary,
            'content': content,
            'tags': [BOOK],
            'country': COUNTRY,
            'culture': COUNTRY,
            'author': AUTHOR,
            'collection': BOOK,
            'source': SOURCE,
            'popularity': 4,
            'duration': max(1, round(len(content) / 300)),
            'ageMin': 8,
            'ageMax': 13,
            'safetyChecked': True,
            'version': '1.0.0',
        })
    return objs


def main():
    chapters = parse()
    objs = build(chapters)
    log = []
    log.append('解析章节数: %d  -> 有效条目: %d' % (len(chapters), len(objs)))
    for o in objs:
        log.append('  [%5d字 %2d分钟] %s' % (len(o['content']), o['duration'], o['title']))

    # ---------- 校验（全部放在写回之前） ----------
    errs = []
    if len(objs) != 19:
        errs.append('章节数应为 19，实际 %d' % len(objs))
    ids = [o['id'] for o in objs]
    if len(set(ids)) != len(ids):
        errs.append('id 重复')
    for o in objs:
        if len(o['content']) < 120:
            errs.append('过短: ' + o['title'])
        if any(k in o['content'] for k in ('图书在版编目', 'ISBN', '扫一扫', '产品经理')):
            errs.append('噪声残留: ' + o['title'])

    lib = open(LIB, encoding='utf-8').read()
    try:
        old = json.loads(lib[lib.index('['):lib.rindex(']') + 1])
    except Exception as e:
        errs.append('原库 JSON 破损: %s' % e)
        old = []
    exist = set(x['id'] for x in old)
    dup = [o['id'] for o in objs if o['id'] in exist]
    if dup:
        errs.append('与库内 id 冲突: %s' % dup[:3])

    log.append('')
    log.append('原库篇数: %d -> 追加后: %d' % (len(old), len(old) + len(objs)))
    log.append('校验: %s' % ('通过' if not errs else '失败 -> ' + '; '.join(errs)))
    if errs:
        open('G:/gpt/_dd_result.txt', 'w', encoding='utf-8').write('\n'.join(log))
        return

    # ---------- 追加写回（先备份）----------
    shutil.copyfile(LIB, LIB + '.bak_dulide')
    tail = '\n}];'
    pos = lib.rindex(tail) + 2          # +2 = 跳过 "\n}"，停在旧对象闭合括号之后
    add = ',\n' + ',\n'.join(json.dumps(o, ensure_ascii=False, indent=2) for o in objs)
    new = lib[:pos] + add + lib[pos:]

    # 写回前再次确认新内容可解析
    try:
        chk = json.loads(new[new.index('['):new.rindex(']') + 1])
        log.append('写回前 JSON 复检: OK (%d 篇)' % len(chk))
    except Exception as e:
        log.append('写回前 JSON 复检失败，已中止：%s' % e)
        open('G:/gpt/_dd_result.txt', 'w', encoding='utf-8').write('\n'.join(log))
        return

    open(LIB, 'w', encoding='utf-8', newline='').write(new)
    log.append('已写入: %s' % LIB)
    open('G:/gpt/_dd_result.txt', 'w', encoding='utf-8').write('\n'.join(log))


if __name__ == '__main__':
    main()
