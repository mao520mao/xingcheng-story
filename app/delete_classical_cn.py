# -*- coding: utf-8 -*-
"""删除 cn_stories.jsonl 中仍为纯文言文的篇目（非 AI 前提下网上无真实白话版）。
判定与检测脚本一致：古密度>35 且 现代词密度<4。
"""
import os, json, re

WS = "G:/gpt/星橙故事铺腾讯/app"
PATH = os.path.join(WS, "cn_stories.jsonl")

CL = ['之','乎','者','也','矣','焉','哉','兮','夫','盖','遂','辄','尝','曰','吾','汝','尔','其','君','然','故','乃']
MD = ['的','了','吗','呢','吧','把','被','着','我们','他们','现在','因为','所以','但是','就','这','那','他','她','你']
def dens(t, c):
    n = sum(t.count(x) for x in c); return round(n*1000/max(1,len(t)),1)
def is_pure_cl(c):
    g = dens(c, CL); m = dens(c, MD); return g > 35 and m < 4

rows = [json.loads(l) for l in open(PATH, encoding="utf-8") if l.strip()]
keep, removed = [], []
for r in rows:
    if is_pure_cl(r.get("content", "")):
        removed.append(r["title"])
    else:
        keep.append(r)

with open(PATH, "w", encoding="utf-8") as f:
    for r in keep:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"删除纯文言文 {len(removed)} 篇: {removed}")
print(f"保留 {len(keep)} 篇 -> {PATH}")
