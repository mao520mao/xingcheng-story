# -*- coding: utf-8 -*-
"""联网搜集「历史趣事」：从维基百科取白话正文，逐字繁→简（OpenCC），不改写、非 AI 生成。
选取明代及以前（含明）的真实历史轶事 / 名人事迹，每篇标注出处（维基条目 + 原始史籍）。
输出 history_stories.jsonl，再由 assemble_history.py 生成 js/stories_history.js。
"""
import sys, os, re, json, time, argparse, urllib.request, urllib.parse

VENV_SITE = "/c/Users/Administrator/.workbuddy/binaries/python/envs/default/Lib/site-packages"
sys.path.insert(0, VENV_SITE)
from opencc import OpenCC
cc = OpenCC("t2s")

WS = "G:/gpt/星橙故事铺腾讯/app"
JSONL = os.path.join(WS, "history_stories.jsonl")

# 20 篇：明代及以前真实历史轶事 / 名人事迹（维基百科条目 + 锚点 + 原始史籍出处）
PLAN = [
    {"wiki":"曹冲",      "anchor":"秤象", "title":"曹冲称象",       "era":"三国·魏", "record":"《三国志·魏书·武文世王公传》"},
    {"wiki":"司马光",    "anchor":"瓮",   "title":"司马光砸缸",     "era":"北宋",     "record":"《宋史·司马光传》"},
    {"wiki":"匡衡",      "anchor":"壁",   "title":"匡衡凿壁偷光",   "era":"西汉",     "record":"《西京杂记》"},
    {"wiki":"车胤",      "anchor":"萤",   "title":"车胤囊萤夜读",   "era":"东晋",     "record":"《晋书·车胤传》"},
    {"wiki":"祖逖",      "anchor":"鸡",   "title":"祖逖闻鸡起舞",   "era":"东晋",     "record":"《晋书·祖逖传》"},
    {"wiki":"勾践",      "anchor":"尝胆", "title":"越王勾践卧薪尝胆","era":"春秋",     "record":"《史记·越王勾践世家》"},
    {"wiki":"蔺相如",    "anchor":"和氏璧","title":"蔺相如完璧归赵", "era":"战国",     "record":"《史记·廉颇蔺相如列传》"},
    {"wiki":"王羲之",    "anchor":"墨",   "title":"王羲之临池学书", "era":"东晋",     "record":"《晋书·王羲之传》"},
    {"wiki":"王冕",      "anchor":"长明灯", "title":"王冕寺中苦读",   "era":"元",       "record":"宋濂《王冕传》"},
    {"wiki":"岳飞",      "anchor":"精忠", "title":"岳飞精忠报国",   "era":"南宋",     "record":"《宋史·岳飞传》"},
    {"wiki":"文天祥",    "anchor":"正气", "title":"文天祥浩然正气", "era":"南宋",     "record":"《宋史·文天祥传》"},
    {"wiki":"玄奘",      "anchor":"西域", "title":"玄奘西行取经",   "era":"唐",       "record":"《大唐西域记》"},
    {"wiki":"鉴真",      "anchor":"失明", "title":"鉴真六次东渡",   "era":"唐",       "record":"《唐大和上东征传》"},
    {"wiki":"张衡",      "anchor":"地动", "title":"张衡造地动仪",   "era":"东汉",     "record":"《后汉书·张衡传》"},
    {"wiki":"华佗",      "anchor":"麻沸", "title":"华佗与麻沸散",   "era":"东汉",     "record":"《三国志·方技传·华佗》"},
    {"wiki":"司马迁",    "anchor":"腐刑", "title":"司马迁忍辱著《史记》","era":"西汉", "record":"《汉书·司马迁传》"},
    {"wiki":"诸葛亮",    "anchor":"鞠躬", "title":"诸葛亮鞠躬尽瘁", "era":"三国·蜀", "record":"《三国志·诸葛亮传》"},
    {"wiki":"包拯",      "anchor":"河清", "title":"包拯笑比河清",   "era":"北宋",     "record":"《宋史·包拯传》"},
    {"wiki":"郑和",      "anchor":"西洋", "title":"郑和七下西洋",   "era":"明",       "record":"《明史·郑和传》"},
    {"wiki":"于谦",      "anchor":"北京保卫战", "title":"于谦保卫北京",   "era":"明",       "record":"《明史·于谦传》"},
    # ===== 新增 100 篇（明代及以前真实历史轶事 / 名人事迹，维基百科条目 + 原始史籍出处） =====
    {"wiki":"晏婴", "anchor":"使楚", "title":"晏子使楚", "era":"春秋", "record":"《晏子春秋》"},
    {"wiki":"管仲", "anchor":"鲍叔", "title":"管鲍之交", "era":"春秋", "record":"《史记·管晏列传》"},
    {"wiki":"介子推", "anchor":"割股", "title":"介子推割股奉君", "era":"春秋", "record":"《左传·僖公二十四年》"},
    {"wiki":"孙武", "anchor":"宫女", "title":"孙武演阵斩美姬", "era":"春秋", "record":"《史记·孙子吴起列传》"},
    {"wiki":"季札", "anchor":"挂剑", "title":"季札挂剑", "era":"春秋", "record":"《史记·吴太伯世家》"},
    {"wiki":"曾子", "anchor":"猪", "title":"曾子杀猪", "era":"春秋", "record":"《韩非子·外储说左上》"},
    {"wiki":"豫让", "anchor":"吞炭", "title":"豫让吞炭漆身", "era":"战国", "record":"《史记·刺客列传》"},
    {"wiki":"荆轲", "anchor":"匕首", "title":"荆轲刺秦王", "era":"战国", "record":"《史记·刺客列传》"},
    {"wiki":"扁鹊", "anchor":"蔡桓公", "title":"扁鹊见蔡桓公", "era":"春秋", "record":"《史记·扁鹊仓公列传》"},
    {"wiki":"老子", "anchor":"出关", "title":"老子出关", "era":"春秋", "record":"《史记·老子韩非列传》"},
    {"wiki":"庄子", "anchor":"梦蝶", "title":"庄周梦蝶", "era":"战国", "record":"《庄子·齐物论》"},
    {"wiki":"屈原", "anchor":"汨罗", "title":"屈原投江", "era":"战国", "record":"《史记·屈原贾生列传》"},
    {"wiki":"李斯", "anchor":"逐客", "title":"李斯谏逐客书", "era":"秦", "record":"《史记·李斯列传》"},
    {"wiki":"赵高", "anchor":"指鹿", "title":"赵高指鹿为马", "era":"秦", "record":"《史记·秦始皇本纪》"},
    {"wiki":"蒙恬", "anchor":"笔", "title":"蒙恬造笔", "era":"秦", "record":"《史记·蒙恬列传》"},
    {"wiki":"项羽", "anchor":"破釜", "title":"项羽破釜沉舟", "era":"秦末", "record":"《史记·项羽本纪》"},
    {"wiki":"刘邦", "anchor":"白蛇", "title":"刘邦斩白蛇", "era":"汉", "record":"《史记·高祖本纪》"},
    {"wiki":"韩信", "anchor":"胯下", "title":"韩信胯下之辱", "era":"汉", "record":"《史记·淮阴侯列传》"},
    {"wiki":"张良", "anchor":"孺子", "title":"张良圯上受书", "era":"汉", "record":"《史记·留侯世家》"},
    {"wiki":"萧何", "anchor":"韩信", "title":"萧何月下追韩信", "era":"汉", "record":"《史记·萧相国世家》"},
    {"wiki":"苏武", "anchor":"牧羊", "title":"苏武牧羊", "era":"西汉", "record":"《汉书·苏武传》"},
    {"wiki":"李广", "anchor":"飞将", "title":"李广难封", "era":"西汉", "record":"《史记·李将军列传》"},
    {"wiki":"卫青", "anchor":"漠北", "title":"卫青漠北之战", "era":"西汉", "record":"《史记·卫将军骠骑列传》"},
    {"wiki":"霍去病", "anchor":"封狼", "title":"霍去病封狼居胥", "era":"西汉", "record":"《史记·卫将军骠骑列传》"},
    {"wiki":"班超", "anchor":"投笔", "title":"班超投笔从戎", "era":"东汉", "record":"《后汉书·班超传》"},
    {"wiki":"杨震", "anchor":"四知", "title":"杨震四知拒金", "era":"东汉", "record":"《后汉书·杨震传》"},
    {"wiki":"黄香", "anchor":"扇枕", "title":"黄香扇枕温衾", "era":"东汉", "record":"《东观汉记·黄香》"},
    {"wiki":"孔融", "anchor":"让梨", "title":"孔融让梨", "era":"东汉", "record":"《世说新语·家戒》"},
    {"wiki":"陈寔", "anchor":"梁上", "title":"陈寔与梁上君子", "era":"东汉", "record":"《后汉书·陈寔传》"},
    {"wiki":"缇萦", "anchor":"救父", "title":"缇萦救父", "era":"西汉", "record":"《史记·扁鹊仓公列传》"},
    {"wiki":"张骞", "anchor":"西域", "title":"张骞出使西域", "era":"西汉", "record":"《史记·大宛列传》"},
    {"wiki":"蔡伦", "anchor":"造纸", "title":"蔡伦造纸", "era":"东汉", "record":"《后汉书·蔡伦传》"},
    {"wiki":"曹操", "anchor":"望梅", "title":"曹操望梅止渴", "era":"三国", "record":"《世说新语·假谲》"},
    {"wiki":"刘备", "anchor":"三顾", "title":"刘备三顾茅庐", "era":"三国", "record":"《三国志·诸葛亮传》注"},
    {"wiki":"关羽", "anchor":"刮骨", "title":"关羽刮骨疗毒", "era":"三国", "record":"《三国志·关羽传》"},
    {"wiki":"赵云", "anchor":"长坂", "title":"赵云长坂坡", "era":"三国", "record":"《三国志·赵云传》"},
    {"wiki":"周瑜", "anchor":"赤壁", "title":"周瑜赤壁之战", "era":"三国", "record":"《三国志·周瑜传》"},
    {"wiki":"曹植", "anchor":"七步", "title":"曹植七步诗", "era":"三国", "record":"《世说新语·文学》"},
    {"wiki":"杨修", "anchor":"鸡肋", "title":"杨修鸡肋", "era":"三国", "record":"《世说新语·捷悟》"},
    {"wiki":"吕蒙", "anchor":"刮目", "title":"吕蒙刮目相看", "era":"三国", "record":"《三国志·吕蒙传》注"},
    {"wiki":"张飞", "anchor":"当阳", "title":"张飞喝断当阳桥", "era":"三国", "record":"《三国志·张飞传》"},
    {"wiki":"陶侃", "anchor":"运甓", "title":"陶侃运甓", "era":"东晋", "record":"《晋书·陶侃传》"},
    {"wiki":"周处", "anchor":"三害", "title":"周处除三害", "era":"西晋", "record":"《晋书·周处传》"},
    {"wiki":"顾恺之", "anchor":"点睛", "title":"顾恺之画龙点睛", "era":"东晋", "record":"《晋书·顾恺之传》"},
    {"wiki":"谢安", "anchor":"东山", "title":"谢安东山再起", "era":"东晋", "record":"《晋书·谢安传》"},
    {"wiki":"左思", "anchor":"三都", "title":"左思洛阳纸贵", "era":"西晋", "record":"《晋书·左思传》"},
    {"wiki":"葛洪", "anchor":"炼丹", "title":"葛洪炼丹著书", "era":"东晋", "record":"《晋书·葛洪传》"},
    {"wiki":"王献之", "anchor":"书法", "title":"王献之习字", "era":"东晋", "record":"《晋书·王献之传》"},
    {"wiki":"祖冲之", "anchor":"圆周", "title":"祖冲之圆周率", "era":"南朝宋", "record":"《南史·祖冲之传》"},
    {"wiki":"郦道元", "anchor":"水经", "title":"郦道元水经注", "era":"北魏", "record":"《北史·郦道元传》"},
    {"wiki":"江革", "anchor":"行佣", "title":"江革行佣供母", "era":"南朝梁", "record":"《梁书·江革传》"},
    {"wiki":"陶弘景", "anchor":"山中宰相", "title":"陶弘景山中宰相", "era":"南朝梁", "record":"《南史·陶弘景传》"},
    {"wiki":"赵绰", "anchor":"执法", "title":"赵绰执法", "era":"隋", "record":"《隋书·赵绰传》"},
    {"wiki":"韩擒虎", "anchor":"陈", "title":"韩擒虎灭陈", "era":"隋", "record":"《隋书·韩擒虎传》"},
    {"wiki":"隋文帝", "anchor":"开皇", "title":"隋文帝开皇之治", "era":"隋", "record":"《隋书·高祖纪》"},
    {"wiki":"李白", "anchor":"力士", "title":"李白力士脱靴", "era":"唐", "record":"《唐才子传·李白》"},
    {"wiki":"杜甫", "anchor":"草堂", "title":"杜甫草堂", "era":"唐", "record":"《旧唐书·杜甫传》"},
    {"wiki":"白居易", "anchor":"顾况", "title":"白居易顾况题名", "era":"唐", "record":"《旧唐书·白居易传》"},
    {"wiki":"韩愈", "anchor":"鳄鱼", "title":"韩愈祭鳄鱼", "era":"唐", "record":"《旧唐书·韩愈传》"},
    {"wiki":"柳宗元", "anchor":"柳州", "title":"柳宗元治柳州", "era":"唐", "record":"《旧唐书·柳宗元传》"},
    {"wiki":"颜真卿", "anchor":"祭侄", "title":"颜真卿祭侄文稿", "era":"唐", "record":"《旧唐书·颜真卿传》"},
    {"wiki":"怀素", "anchor":"芭蕉", "title":"怀素芭蕉练字", "era":"唐", "record":"《唐才子传·怀素》"},
    {"wiki":"魏徵", "anchor":"镜子", "title":"魏徵以人为镜", "era":"唐", "record":"《旧唐书·魏徵传》"},
    {"wiki":"娄师德", "anchor":"唾面", "title":"娄师德唾面自干", "era":"唐", "record":"《旧唐书·娄师德传》"},
    {"wiki":"郭子仪", "anchor":"单骑", "title":"郭子仪单骑退回纥", "era":"唐", "record":"《旧唐书·郭子仪传》"},
    {"wiki":"孟郊", "anchor":"游子", "title":"孟郊游子吟", "era":"唐", "record":"《旧唐书·孟郊传》"},
    {"wiki":"贺知章", "anchor":"金龟", "title":"贺知章金龟换酒", "era":"唐", "record":"《旧唐书·贺知章传》"},
    {"wiki":"贾岛", "anchor":"推敲", "title":"贾岛推敲", "era":"唐", "record":"《唐才子传·贾岛》"},
    {"wiki":"薛仁贵", "anchor":"三箭", "title":"薛仁贵三箭定天山", "era":"唐", "record":"《旧唐书·薛仁贵传》"},
    {"wiki":"阎立本", "anchor":"步辇", "title":"阎立本步辇图", "era":"唐", "record":"《旧唐书·阎立本传》"},
    {"wiki":"冯道", "anchor":"长乐", "title":"冯道历仕", "era":"五代", "record":"《旧五代史·冯道传》"},
    {"wiki":"钱镠", "anchor":"射潮", "title":"钱镠射潮筑塘", "era":"吴越", "record":"《旧五代史·钱镠传》"},
    {"wiki":"范仲淹", "anchor":"画粥", "title":"范仲淹断齑画粥", "era":"北宋", "record":"《宋史·范仲淹传》"},
    {"wiki":"欧阳修", "anchor":"画荻", "title":"欧阳修画荻教子", "era":"北宋", "record":"《宋史·欧阳修传》"},
    {"wiki":"苏轼", "anchor":"东坡", "title":"苏轼东坡躬耕", "era":"北宋", "record":"《宋史·苏轼传》"},
    {"wiki":"苏洵", "anchor":"二十七", "title":"苏洵大器晚成", "era":"北宋", "record":"《宋史·苏洵传》"},
    {"wiki":"王安石", "anchor":"变法", "title":"王安石变法", "era":"北宋", "record":"《宋史·王安石传》"},
    {"wiki":"沈括", "anchor":"梦溪", "title":"沈括梦溪笔谈", "era":"北宋", "record":"《宋史·沈括传》"},
    {"wiki":"毕昇", "anchor":"活字", "title":"毕昇活字印刷", "era":"北宋", "record":"《梦溪笔谈》"},
    {"wiki":"杨时", "anchor":"立雪", "title":"杨时程门立雪", "era":"北宋", "record":"《宋史·杨时传》"},
    {"wiki":"朱熹", "anchor":"鹅湖", "title":"朱熹鹅湖之会", "era":"南宋", "record":"《宋史·朱熹传》"},
    {"wiki":"陆游", "anchor":"示儿", "title":"陆游示儿诗", "era":"南宋", "record":"《宋史·陆游传》"},
    {"wiki":"辛弃疾", "anchor":"南归", "title":"辛弃疾南归", "era":"南宋", "record":"《宋史·辛弃疾传》"},
    {"wiki":"寇准", "anchor":"澶渊", "title":"寇准澶渊之盟", "era":"北宋", "record":"《宋史·寇准传》"},
    {"wiki":"黄庭坚", "anchor":"书法", "title":"黄庭坚书法", "era":"北宋", "record":"《宋史·黄庭坚传》"},
    {"wiki":"周敦颐", "anchor":"爱莲", "title":"周敦颐爱莲说", "era":"北宋", "record":"《宋史·周敦颐传》"},
    {"wiki":"张载", "anchor":"横渠", "title":"张载横渠四句", "era":"北宋", "record":"《宋史·张载传》"},
    {"wiki":"关汉卿", "anchor":"窦娥", "title":"关汉卿窦娥冤", "era":"元", "record":"《录鬼簿》"},
    {"wiki":"郭守敬", "anchor":"授时", "title":"郭守敬授时历", "era":"元", "record":"《元史·郭守敬传》"},
    {"wiki":"黄道婆", "anchor":"纺织", "title":"黄道婆纺织", "era":"元", "record":"《辍耕录》"},
    {"wiki":"赵孟頫", "anchor":"书画", "title":"赵孟頫书画", "era":"元", "record":"《元史·赵孟頫传》"},
    {"wiki":"马致远", "anchor":"汉宫", "title":"马致远汉宫秋", "era":"元", "record":"《录鬼簿》"},
    {"wiki":"王阳明", "anchor":"龙场", "title":"王阳明龙场悟道", "era":"明", "record":"《明史·王守仁传》"},
    {"wiki":"海瑞", "anchor":"棺", "title":"海瑞备棺上疏", "era":"明", "record":"《明史·海瑞传》"},
    {"wiki":"张居正", "anchor":"一条鞭", "title":"张居正改革", "era":"明", "record":"《明史·张居正传》"},
    {"wiki":"汤显祖", "anchor":"牡丹亭", "title":"汤显祖牡丹亭", "era":"明", "record":"《明史·汤显祖传》"},
    {"wiki":"徐霞客", "anchor":"游记", "title":"徐霞客游记", "era":"明", "record":"《徐霞客游记》"},
    {"wiki":"李时珍", "anchor":"本草", "title":"李时珍本草纲目", "era":"明", "record":"《明史·李时珍传》"},
    {"wiki":"宋应星", "anchor":"天工", "title":"宋应星天工开物", "era":"明", "record":"《天工开物》"},
    {"wiki":"杨慎", "anchor":"临江仙", "title":"杨慎临江仙", "era":"明", "record":"《明史·杨慎传》"},
]

def api(params):
    params = dict(params); params["redirects"] = "1"  # 解析维基重定向，避免取到「简繁重定向」说明页
    url = "https://zh.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent":"StoryCollectBot/1.0 (research)"})
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(20); continue
            raise

def fetch_extract(title):
    d = api({"action":"query","prop":"extracts","explaintext":"1",
             "titles":title,"format":"json","formatversion":"2"})
    pages = d.get("query",{}).get("pages",[])
    if not pages: return ""
    return pages[0].get("extract","") or ""

def split_sections(text):
    """Return list of (header, body) for === headers. Lead (no header) kept as header=''."""
    parts = re.split(r'^(={2,4})\s*(.+?)\s*\1\s*$', text, flags=re.M)
    # parts: [lead, =level, header, body, =level, header, body, ...]
    secs = []
    lead = parts[0].strip()
    if lead:
        secs.append(("", lead))
    i = 1
    while i+3 <= len(parts):
        level, header, body = parts[i], parts[i+1], parts[i+2]
        body = body.strip()
        if body:
            secs.append((header.strip(), body))
        i += 3
    return secs

def extract_anecdote(text, anchor):
    simp = cc.convert(text)
    secs = split_sections(simp)
    # 1) prefer a section whose HEADER or BODY contains the anchor
    #    （锚点常为章节标题名，如「北京保卫战」，标题不在正文内，故标题也要匹配）
    for hdr, body in secs:
        if anchor in hdr or anchor in body:
            return body, hdr
    # 2) fallback: any paragraph containing anchor
    paras = re.split(r'\n{2,}', simp)
    for p in paras:
        if anchor in p:
            return p.strip(), ""
    # 3) last resort: lead (first 2 paragraphs)
    return (secs[0][1] if secs else simp[:600]), ""

def trim_story(body, max_chars=900):
    # keep coherent: split into paragraphs, accumulate until max
    paras = [p.strip() for p in re.split(r'\n{2,}', body) if p.strip()]
    out, n = [], 0
    for p in paras:
        if n + len(p) > max_chars and out:
            break
        out.append(p); n += len(p)
    return "\n\n".join(out).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--count", type=int, default=len(PLAN))
    a = ap.parse_args()
    items = PLAN[a.offset:a.offset+a.count]
    # load existing (avoid dup within this run file)
    done = set()
    if os.path.exists(JSONL):
        for line in open(JSONL, encoding="utf-8"):
            line=line.strip()
            if not line: continue
            try: done.add(json.loads(line)["title"])
            except: pass
    added = 0
    for it in items:
        if it["title"] in done:
            print(f"  [skip dup] {it['title']}")
            continue
        raw = fetch_extract(it["wiki"])
        if not raw:
            print(f"  [WARN] 未取到 {it['wiki']} 正文")
            continue
        body, hdr = extract_anecdote(raw, it["anchor"])
        story = trim_story(body)
        if len(story) < 40:
            print(f"  [WARN] {it['title']} 正文过短({len(story)})，可能锚点未命中")
        rec = {
            "title": it["title"],
            "content": story,
            "source": f"维基百科《{it['wiki']}》条目，据{it['record']}",
            "author": it["record"],
            "culture": "中国历史",
            "era": it["era"],
            "cat": "history",
            "tags": ["历史趣事"],
        }
        with open(JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        added += 1
        print(f"  [+{added}] {it['title']}  ({it['era']}, {len(story)}字) 锚点命中段: {hdr or '(段落/导语)'}")
        time.sleep(1.2)
    print(f"[batch done] added_this_batch={added} total_in_jsonl={sum(1 for _ in open(JSONL,encoding='utf-8')) if os.path.exists(JSONL) else 0}")

if __name__ == "__main__":
    main()
