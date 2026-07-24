// -*- coding: utf-8 -*-
// 全面校验四个故事库：文言文残留 / duration 字段 / 总量 / 1分钟文章
const fs = require("fs");
const path = require("path");

const JS = "G:/gpt/星橙故事铺腾讯/app/js";
const FILES = {
  CN:     { file: "stories_cn.js",     var: "STORY_LIBRARY_CN" },
  HISTORY: { file: "stories_history.js", var: "STORY_LIBRARY_HISTORY" },
  DATA:   { file: "stories_data.js",   var: "STORY_LIBRARY_EXT" },
  USER:   { file: "stories_user.js",   var: "STORY_LIBRARY_USER" },
};

function load(name, file, v) {
  const code = fs.readFileSync(path.join(JS, file), "utf-8");
  const win = {};
  new Function("window", code)(win);
  return win[v] || [];
}

// 文言文检测（与 python 端一致）：古字密度>35 且 现代词密度<4（每千字）
const CL = "之乎者也矣焉哉兮夫盖遂辄尝曰吾汝尔其君然故乃".split("");
const MD = "的了吗呢吧把被着我们他们现在因为所以但是就这那他她你".split("");
function isPureClassical(text) {
  if (!text || text.length < 80) return false;
  const n = text.length;
  let cl = 0, md = 0;
  for (const ch of text) {
    if (CL.includes(ch)) cl++;
    if (MD.includes(ch)) md++;
  }
  const perK = (x) => (x / n) * 1000;
  const clD = perK(cl), mdD = perK(md);
  return clD > 35 && mdD < 4;
}

let total = 0;
let classicalResidue = [];
let missingDuration = [];
let oneMin = [];
let noMinuteShown = []; // duration 缺失或 <1

for (const [key, cfg] of Object.entries(FILES)) {
  const arr = load(key, cfg.file, cfg.var);
  console.log(`\n[${key}] ${cfg.file} -> ${arr.length} 篇`);
  total += arr.length;
  for (const s of arr) {
    const content = (s.content || s.summary || "").toString();
    if (isPureClassical(content)) {
      classicalResidue.push({ lib: key, id: s.id, title: s.title });
    }
    // duration 字段检查
    if (s.duration === undefined || s.duration === null) {
      missingDuration.push({ lib: key, id: s.id, title: s.title });
    } else {
      if (Number(s.duration) === 1) oneMin.push({ lib: key, id: s.id, title: s.title });
      if (Number(s.duration) < 1) noMinuteShown.push({ lib: key, id: s.id, title: s.title, duration: s.duration });
    }
  }
}

console.log("\n========== 校验汇总 ==========");
console.log(`总量: ${total} 篇 (期望 403)`);
console.log(`纯文言文残留: ${classicalResidue.length} 篇`);
if (classicalResidue.length) console.log("  ", JSON.stringify(classicalResidue, null, 0));
console.log(`duration 字段缺失: ${missingDuration.length} 篇`);
if (missingDuration.length) console.log("  ", JSON.stringify(missingDuration.slice(0,20), null, 0));
console.log(`duration==1 (1分钟文章): ${oneMin.length} 篇`);
if (oneMin.length) console.log("  ", JSON.stringify(oneMin, null, 0));
console.log(`duration<1 (异常时长): ${noMinuteShown.length} 篇`);
if (noMinuteShown.length) console.log("  ", JSON.stringify(noMinuteShown.slice(0,20), null, 0));

const ok = classicalResidue.length === 0 && missingDuration.length === 0 && oneMin.length === 0 && total === 403;
console.log("\n结论:", ok ? "✅ 全部通过" : "❌ 存在问题");
process.exit(ok ? 0 : 1);
