#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""后台监督器：每跨过 50 篇翻译节点，写一条带时间戳的进度到 /tmp/translate_monitor.log"""
import json, time, os

APP_DIR = os.path.join(os.path.dirname(__file__ or '.'))
PATH = os.path.join(APP_DIR, 'js', 'stories_data.js')
LOG = '/tmp/translate_monitor.log'
TOTAL = 386

def get_count():
    try:
        raw = open(PATH, encoding='utf-8').read()
        js = raw.split('window.STORY_LIBRARY_EXT =', 1)[1].rstrip().rstrip(';')
        lib = json.loads(js)
        return len(lib)
    except Exception:
        return 0

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + '  ' + msg + '\n')
        f.flush()

last_reported = -50
log(f'监督器启动 | 总数目标 {TOTAL}')

while True:
    c = get_count()
    if c > 0 and c > last_reported:
        milestone = (c // 50) * 50
        if milestone > last_reported and milestone > 0:
            log(f'里程碑 {milestone}/{TOTAL} | 已翻译 {milestone} | 未翻译 {TOTAL - milestone} | 总数 {TOTAL}')
            last_reported = milestone
    if c >= TOTAL:
        log(f'全部完成 {TOTAL}/{TOTAL} | 已翻译 {TOTAL} | 未翻译 0 | 总数 {TOTAL}')
        break
    time.sleep(20)
log('监督器结束')
