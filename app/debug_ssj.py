# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, "G:/gpt/星橙故事铺腾讯/app")
sys.path.insert(0, "/c/Users/Administrator/.workbuddy/binaries/python/envs/default/Lib/site-packages")
import fetch_cn_library as F

# debug 搜神記/第11卷
vol = F.fetch_page("搜神記/第11卷")
print("=== vol text len:", len(vol))
print("=== first 1200 chars ===")
print(vol[:1200])
print("\n=== split_tales block count:", len(F.split_tales(vol)))
for i, b in enumerate(F.split_tales(vol)[:6]):
    print(f"\n--- block {i} (len {len(b)}) ---")
    print(b[:200])
print("\n=== find_block 干将莫邪 ===")
fb = F.find_block(vol, "干将莫邪")
print("found:", fb is not None, (fb[:150] if fb else ""))
print("\n=== find_block 韩凭 ===")
fb2 = F.find_block(vol, "韩凭")
print("found:", fb2 is not None, (fb2[:150] if fb2 else ""))
