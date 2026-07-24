#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""监督翻译进度：每跨过 50 篇节点，打印一次 已翻译/未翻译/总数。"""
import json, time, os

ZH = os.path.join(os.path.dirname(__file__ or '.'), 'js', 'stories_data.js')
TOTAL = 386
MILE = 50
MAX_SEC = 540  # 约 9 分钟一轮

def count():
    try:
        raw = open(ZH, encoding='utf-8').read()
        if 'window.STORY_LIBRARY_EXT' not in raw:
            return 0
        js = raw.split('window.STORY_LIBRARY_EXT =', 1)[1].rstrip().rstrip(';')
        return len(json.loads(js))
    except Exception:
        return 0

def main():
    last = (count() // MILE) * MILE
    t0 = time.time()
    print(f'[监督] 起点已翻译 {count()}/{TOTAL} | 目标每 {MILE} 篇汇报', flush=True)
    while True:
        n = count()
        m = (n // MILE) * MILE
        if m > last:
            last = m
            print(f'[里程碑 {m}] 已翻译 {n} | 未翻译 {TOTAL-n} | 总数 {TOTAL}', flush=True)
        if n >= TOTAL:
            print(f'[完成] 已翻译 {n}/{TOTAL} | 未翻译 0', flush=True)
            return
        if time.time() - t0 > MAX_SEC:
            print(f'[本轮结束] 当前已翻译 {n} | 未翻译 {TOTAL-n} | 总数 {TOTAL}', flush=True)
            return
        time.sleep(15)

if __name__ == '__main__':
    main()
