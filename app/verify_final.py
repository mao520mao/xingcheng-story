# -*- coding: utf-8 -*-
"""V16 校验：时长字段、文言文替换覆盖率、删除计数、全库总量。"""
import os, re, json
WS = "G:/gpt/星橙故事铺腾讯/app"
FILES = {
    "data": os.path.join(WS, "js", "stories_data.js"),
    "user": os.path.join(WS, "js", "stories_user.js"),
    "cn": os.path.join(WS, "js", "stories_cn.js"),
    "history": os.path.join(WS, "js", "stories_history.js"),
}
CLASSICAL = ["之","乎","者","也","矣","焉","哉","兮","夫","盖","遂","辄","尝","曰","吾","汝","尔","其","故","乃"]
MODERN = ["的","了","吗","呢","吧","把","被","着","我们","他们","现在","因为","所以","但是","就","这","那","他","她"]
def dens(t,c):
    n=sum(t.count(x) for x in c); return round(n*1000/max(1,len(t)),1)
def is_cl(t):
    return dens(t,CLASSICAL)>15 and dens(t,MODERN)<10

print("===== 各数据源 =====")
total=0
for k,path in FILES.items():
    t=open(path,encoding="utf-8").read()
    m=re.search(r"=\s*(\[.*\])\s*;", t, re.S)
    arr=json.loads(m.group(1))
    n=len(arr)
    total+=n
    # duration 字段检查
    no_dur=[s["title"] for s in arr if not isinstance(s.get("duration"),(int,float))]
    # 文言文残留（CN/history 关注）
    cl=[s["title"] for s in arr if is_cl(s.get("content",""))]
    print(f"{k}: {n} 篇 | 缺 duration 字段: {len(no_dur)} | 仍含文言文: {len(cl)}")
    if no_dur: print("   缺duration样例:", no_dur[:5])
    if k in ("cn","history") and cl: print("   残留文言文:", cl[:8])
print(f"\n全库总量: {total} 篇")
