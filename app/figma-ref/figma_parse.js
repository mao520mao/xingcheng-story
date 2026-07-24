// 解析 Figma 文件 JSON，提取页面/画板的尺寸、背景色、文字样式、圆角等关键设计数据
const fs = require('fs');
const data = JSON.parse(fs.readFileSync(process.argv[2] || 'figma_file.json', 'utf8'));

function rgbToHex(c) {
  if (!c) return null;
  const r = Math.round((c.r ?? 0) * 255);
  const g = Math.round((c.g ?? 0) * 255);
  const b = Math.round((c.b ?? 0) * 255);
  const a = c.a == null ? 1 : Math.round(c.a * 100) / 100;
  return `#${[r,g,b].map(v=>v.toString(16).padStart(2,'0')).join('')}${a!==1?` (a=${a})`:''}`;
}

function getFills(node) {
  if (!node.fills || !Array.isArray(node.fills)) return [];
  return node.fills.filter(f => f.visible !== false && f.type === 'SOLID').map(f => ({
    color: rgbToHex(f.color),
    opacity: f.opacity
  }));
}

function walk(node, depth, out, path) {
  if (!node) return;
  const t = node.type;
  // 收集文字
  if (t === 'TEXT' && node.characters) {
    out.texts.push({
      path: path,
      text: node.characters.replace(/\s+/g,' ').slice(0,80),
      fontSize: node.style?.fontSize,
      fontFamily: node.style?.fontFamily,
      fontWeight: node.style?.fontWeight,
      lineHeight: node.style?.lineHeightPx,
      color: getFills(node).map(f=>f.color).join(',') || null,
    });
  }
  if (node.children) node.children.forEach(c => walk(c, depth+1, out, path + '/' + (c.name||c.type)));
}

const doc = data.document;
console.log('=== 顶层结构 ===');
const canvases = doc.children.filter(c => c.type === 'CANVAS');
console.log('画布数:', canvases.length);
canvases.forEach(cv => {
  console.log(`\n📄 画布: ${cv.name} (${cv.id})  子节点数: ${cv.children?.length||0}`);
});

console.log('\n=== 每个画板(Frame)详情 ===');
canvases.forEach(cv => {
  (cv.children||[]).forEach(frame => {
    if (frame.type === 'FRAME' || frame.type === 'COMPONENT' || frame.type === 'INSTANCE') {
      const out = { texts: [] };
      const box = frame.absoluteBoundingBox;
      const w = box?.width, h = box?.height;
      const fills = getFills(frame);
      const radius = frame.cornerRadius;
      console.log(`\n🖼 ${frame.name}  [${frame.id}]  ${w}x${h}  radius=${radius ?? '—'}`);
      console.log('   背景色:', fills.length? fills.map(f=>`${f.color}${f.opacity?`/${f.opacity}`:''}`).join(', ') : '(无/透明)');
      // 递归收集本画板内的文字
      out.texts = [];
      walk(frame, 0, out, frame.name);
      if (out.texts.length) {
        console.log('   文字(' + out.texts.length + '):');
        out.texts.slice(0, 60).forEach(tx => {
          console.log(`     • [${tx.fontSize}px/${tx.fontWeight||'?'} ${tx.fontFamily||''}] ${tx.color||''}  "${tx.text}"`);
        });
      }
    }
  });
});
