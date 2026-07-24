#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前台监督：等待下一个 50 篇里程碑出现并打印，超时则返回 TIMEOUT。
用于逐个里程碑向用户汇报进度。"""
import json, time, os, sys

APP_DIR = os.path.join(os.path.dirname(__file__ or '.'))
PATH = os.path.join(APP_DIR, 'js', 'stories_data.js')
TOTAL = 386
WAIT = int(sys.argv[1]) if len(sys.argv) > 1 else 580  # 默认等待秒数

def cnt():
    try:
        raw = open(PATH, encoding='utf-8').read()
        js = raw.split('window.STORY_LIBRARY_EXT =', 1)[1].rstrip().rstrip(';')
        return len(json.loads(js))
    except Exception:
        return 0

c = cnt()
last = (c // 50) * 50
deadline = time.time() + WAIT
while time.time() < deadline:
    c = cnt()
    m = (c // 50) * 50
    if m > last and m > 0:
        print(f'MILESTONE {m}/{TOTAL} 已翻译 {m} 未翻译 {TOTAL - m} 总数 {TOTAL}')
        sys.exit(0)
    if c >= TOTAL:
        print(f'DONE {TOTAL}/{TOTAL} 已翻译 {TOTAL} 未翻译 0 总数 {TOTAL}')
        sys.exit(0)
    time.sleep(15)
print('TIMEOUT')
sys.exit(2)
