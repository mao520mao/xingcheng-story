/**
 * 星橙故事铺 — 主应用逻辑 v2（基于 Figma 原稿逐像素还原）
 * SPA 路由：图书馆(单卡片轮播) · 朗读页(沉浸式+浮动播放器) · 星藏阁(Tab+封面卡片) · 设置(分区卡片)
 */
(function () {
  'use strict';

  /* 故事数据延迟加载：2.2MB JSON 同步解析会阻塞主线程数百毫秒。
     改为先声明空数组 → 立即渲染 UI → 微任务后异步填充数据 → 再 pickBatch 渲染内容。 */
  var stories = [];
  var _storiesReady = false;
  var _loadTries = 0;
  var _dataLoadFailed = false;   // 数据脚本（stories_data.js）确实未加载/未执行
  var _dataInjected = false;    // 是否已用「无查询串」动态脚本兜底注入过
  function _loadStories(){
    if(_storiesReady) return;                 // 已成功加载，不再重复
    try{
      // V17 起：仅保留「王尔德童话 / 安徒生童话」两库，合并进 STORY_LIBRARY_EXT
      stories = (window.STORY_LIBRARY_EXT || []);
    }catch(e){
      stories = [];
      if(window.console) console.error('story data load failed', e);
    }
    if(!stories.length){
      /* 数据尚未就绪：先持续重试（覆盖「大文件解析稍慢」的情况）。 */
      if(_loadTries < 60){ _loadTries++; setTimeout(_loadStories, 300); }
      /* 重试约 2 秒后仍无数据 → 用「不带 ?v= 查询串」的动态 <script> 二次加载。
         原因：file:///android_asset/ 下，带查询串的静态 <script src="...?v=17">
         可能被 WebView 当成文件名一部分而 404；动态注入干净 URL 给一次补救机会。 */
      if(_loadTries>=7 && !_dataInjected && !window.STORY_LIBRARY_EXT){
        _dataInjected = true;
        try{
          var s=document.createElement('script');
          s.src='js/stories_data.js';           // 干净 URL，无查询串
          s.onload=function(){ _loadTries=0; _loadStories(); };
          s.onerror=function(){ _dataLoadFailed=true; if(view==='library') renderLibrary(); };
          (document.head||document.documentElement).appendChild(s);
        }catch(e){ _dataLoadFailed=true; if(view==='library') renderLibrary(); }
        return;
      }
      /* 重试耗尽且兜底也失败 → 标记加载失败，给出明确提示而非无限转圈 */
      if(_loadTries>=60 && !window.STORY_LIBRARY_EXT){
        _dataLoadFailed = true;
        if(view==='library'){ renderLibrary(); }
      }
      return;
    }
    _storiesReady = true;
    /* 数据就绪后，若当前在图书馆视图则渲染真实卡片 */
    if(view==='library'){
      if(batch.length===0){ batch=pickBatch(); topIndex=0; }
      renderLibrary();
    }
  }
  /* 触发首屏数据加载。
     安卓 WebView 的 requestIdleCallback 可能长期不触发，故用 setTimeout 兜底；
     同时加"未就绪则每 300ms 重试"循环（最多 ~18s），彻底避免永远停在"整理书架"骨架。 */
  if('requestIdleCallback' in window){
    try{ window.requestIdleCallback(_loadStories,{timeout:300}); }catch(e){ /* ignore */ }
  }
  setTimeout(_loadStories, 60);
  /* V17 兴趣偏好：仅 2 个（王尔德 / 安徒生） */
  var PREFS = ['王尔德', '安徒生'];
  /* 偏好 → 故事标签 映射：王尔德→王尔德童话，安徒生→安徒生童话。
     多选取并集；任一选中即纳入对应标签故事。 */
  var PREF_TAG_MAP = { '王尔德': ['王尔德童话'], '安徒生': ['安徒生童话'] };

  var FONTS    = [{ id:'sm', label:'小', px:15 }, { id:'md', label:'标准', px:17 }, { id:'lg', label:'大', px:19 }, { id:'xl', label:'特大', px:21 }];
  var AGES     = [
    { min:8, max:9,  label:'8-9 岁' },
    { min:10,max:11,label:'10-11 岁' },
    { min:12,max:13,label:'12-13 岁' }
  ];

  /* 状态 */
  var view       = 'library';
  var storyId    = null;
  var batch      = [];          // 图书馆当前展示的故事（3 篇）
  var batchIndex = 0;           // 轮播索引（换一批时使用）
  var readDonePool = null;     // 已读完（滚到底 或 音频播完）的故事 ID 集合（null=未初始化）
  var topIndex   = 0;           // 卡片堆叠：当前位于最前（pos 0）的故事索引
  var vaultTab   = 'fav';       // fav | history
  var playerOpen = false;       // 播放器浮层是否展开

  /* 从 localStorage 持久化读取/写入「已读完」池 */
  function loadReadDonePool(){
    try{ var raw=localStorage.getItem('xch_readdone'); return raw?JSON.parse(raw):{}; }catch(e){return {};}
  }
  function saveReadDonePool(pool){
    try{ localStorage.setItem('xch_readdone',JSON.stringify(pool)); }catch(e){}
  }
  function getReadDonePool(){
    if(!readDonePool) readDonePool=loadReadDonePool();
    return readDonePool;
  }
  /* 标记某故事为「已读完」：滚到底 或 音频播完，二者满足其一即记录（永不进入每日推荐）。
     已推荐但没读完的，不在排除集内，允许重复回到每日推荐卡片。 */
  function markReadDone(id){
    if(!id) return;
    var pool=getReadDonePool();
    if(!pool[id]){ pool[id]=Date.now(); saveReadDonePool(pool); }
  }

  /* 统一图标（描边/填充风格，跟随 currentColor 着色，取代 emoji） */
  var ICONS = {
    refresh:  '<svg class="ico-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 12a8.5 8.5 0 1 1-2.46-5.97"/><path d="M20.5 3.5V9H15"/></svg>',
    book:     '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 5.2A2.2 2.2 0 0 1 5.2 3H11v15H5.2A2.2 2.2 0 0 0 3 20.2V5.2zM21 5.2A2.2 2.2 0 0 0 18.8 3H13v15h5.8a2.2 2.2 0 0 1 2.2 2.2V5.2z"/></svg>',
    pause:    '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6.5" y="5" width="3.6" height="14" rx="1.6"/><rect x="13.9" y="5" width="3.6" height="14" rx="1.6"/></svg>',
    play:     '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.2v13.6L19 12 8 5.2z"/></svg>',
    close:    '<svg class="ico-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    skipBack: '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M11 5.5v13L5 12l6-6.5zM19.5 5.5v13L13.5 12l6-6.5z"/></svg>',
    skipFwd:  '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13 5.5v13L19 12l-6-6.5zM4.5 5.5v13L10.5 12l-6-6.5z"/></svg>',
    voice:    '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3z"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0h-2a4.5 4.5 0 0 1-9 0H5.5z"/><rect x="10.7" y="17" width="2.6" height="4" rx="1.2"/></svg>',
    home:     '<svg class="ico-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M4 11l8-6 8 6"/><path d="M6 9.5V19h12V9.5"/><path d="M10 19v-5h4v5"/></svg>',
    /* 设置页分区图标（填充，跟随 .set-section-title 着色） */
    moon:     '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
    sparkle:  '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l1.9 6.1L20 10l-6.1 1.9L12 18l-1.9-6.1L4 10l6.1-1.9z"/></svg>',
    display:  '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="4" y="4" width="16" height="11" rx="2"/><rect x="10" y="17" width="4" height="3" rx="1"/></svg>',
    storage:  '<svg class="ico-svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/></svg>',
    /* 设置页偏好图标（描边，跟随 .pref-card 着色） */
    castle:   '<svg class="ico-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M4 21V9l3-3 3 3v-3l2-2 2 2v3l3-3 3 3v12z"/><path d="M10 21v-5h4v5"/></svg>',
    bookStroke:'<svg class="ico-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M4 5a2 2 0 0 1 2-2h5v15H6a2 2 0 0 0-2 2V5zM20 5a2 2 0 0 0-2-2h-5v15h5a2 2 0 0 1 2 2V5z"/></svg>',
    leaf:     '<svg class="ico-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 19c0-8 6-14 14-14 0 8-6 14-14 14z"/><path d="M5 19c4-4 8-6 12-7"/></svg>',
    rocket:   '<svg class="ico-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3c3 2 5 6 5 10l-3 3h-4l-3-3c0-4 2-8 5-10z"/><circle cx="12" cy="10" r="2"/><path d="M9 16l-2.5 4 4-1zM15 16l2.5 4-4-1z"/></svg>',
    myth:     '<svg class="ico-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M16.9 16.9l2.1 2.1M4.9 19.1l2.1-2.1M16.9 7.1l2.1-2.1"/></svg>',
    history:  '<svg class="ico-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 4h9a2 2 0 0 1 2 2v12a2 2 0 0 0 2 2H8a2 2 0 0 1-2-2V4z"/><path d="M6 4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2"/><path d="M9.5 9.5l1.4 2.2 2.6-3.4M9.5 15h4"/></svg>'
  };

  /* DOM 引用 */
  var $app  = document.getElementById('screen');
  var $nav  = document.getElementById('bottomNav');

  /* ---------- 工具函数 ---------- */
  function $(s,r){ return(r||document).querySelector(s); }
  function $$(s,r){ return[].slice.call((r||document).querySelectorAll(s)); }
  function el(h){
    var t=document.createElement('template'); t.innerHTML=h.trim();
    return t.content.firstChild;
  }
  function esc(s){
    return String(s).replace(/[&<>"']/g,function(c){
      return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }
  function find(id){ return stories.find(function(s){return s.id===id;}); }

  /* ---------- 星橙 IP SVG 插画 ---------- */
  function mascot(opts){
    opts=opts||{}; var v=opts.variant||'smile'; var w=opts.size||120;
    var leaf='<path d="M62 6 q14 -10 22 -2 q-6 12 -22 6 z" fill="#7BC47F"/>';
    var eyes;
    if(v==='sleep'){
      eyes='<path d="M44 62 q6 6 12 0" stroke="#3a2a1a" stroke-width="3" fill="none" stroke-linecap="round"/>'
          +'<path d="M64 62 q6 6 12 0" stroke="#3a2a1a" stroke-width="3" fill="none" stroke-linecap="round"/>';
    }else{
      eyes='<circle cx="50" cy="60" r="6" fill="#3a2a1a"/><circle cx="70" cy="60" r="6" fill="#3a2a1a"/>'
           +(v==='happy'?'':'<circle cx="48" cy="58" r="2" fill="#fff"/><circle cx="68" cy="58" r="2" fill="#fff"/>');
    }
    var mouth= v==='happy'
      ? '<path d="M50 74 q10 12 20 0" stroke="#3a2a1a" stroke-width="3" fill="none" stroke-linecap="round"/>'
      : '<path d="M54 74 q6 5 12 0" stroke="#3a2a1a" stroke-width="3" fill="none" stroke-linecap="round"/>';
    return '<svg width="'+w+'" height="'+w+'" viewBox="0 0 120 120" xmlns="http://www.w3.org/200/svg" role="img">'
      +'<defs>'
      +'<radialGradient id="sg"><stop offset="0%" stop-color="#fff4dc"/><stop offset="100%" stop-color="#ffdca6"/></radialGradient>'
      +'<radialGradient id="hg"><stop offset="0%" stop-color="#ffb04d"/><stop offset="100%" stop-color="#f2841a"/></radialGradient>'
      +'</defs>'
      +'<circle cx="60" cy="58" r="52" fill="#ff9f1c" opacity=".12"/>'
      +'<path d="M60,10 L72.34,43.01 L107.55,44.55 L79.97,66.49 L89.39,100.45 L60,81 L30.61,100.45 L40.03,66.49 L12.45,44.55 L47.66,43.01 Z" fill="url(#sg)" stroke="#ffe9c2" stroke-width="1.5"/>'
      +'<path d="M34 22 a26 20 0 0 1 52 0 q-26 -14 -52 0 z" fill="url(#hg)"/>'
      +leaf+'<circle cx="42" cy="70" r="5" fill="#ff9bb0" opacity=".55"/><circle cx="78" cy="70" r="5" fill="#ff9bb0" opacity=".55"/>'
      +eyes+mouth+'</svg>';
  }

  /* ---------- 小组件 ---------- */
  function starRow(n){
    var s=''; for(var i=1;i<=5;i++) s+='<span class="'+(i<=n?'filled':'')+'">★</span>'; return '<span class="stars-row">'+s+'</span>';
  }
  function tagPills(tags,cls){
    cls=cls||'';
    return tags.map(function(t){ return '<span class="chip-pill '+cls+'">'+esc(t)+'</span>'; }).join('');
  }
  function toast(msg){
    var t=$('#toast');
    if(!t){t=el('<div id="toast" class="toast"></div>');document.body.appendChild(t);}
    t.textContent=msg;t.classList.add('show');
    clearTimeout(t._timer); t._timer=setTimeout(function(){t.classList.remove('show');},2200);
  }

  /* ========== 推荐算法 ========== */
  function pickBatch(){
    if(!_storiesReady || !stories.length) return [];  /* 数据未就绪，返回空数组 */
    var st=Store.getSettings(); var age=st.age;
    var allPool=stories.filter(function(s){ return s.ageMin<=age && s.ageMax>=age; });
    if(!allPool.length) allPool=stories.slice();
    // 偏好筛选：仅对 PREF_TAG_MAP 中存在的偏好生效（当前为「中国神话」）。
    // 多选时取并集（任一选中偏好命中即入选）；单选中国神话→只推中国神话故事。
    // 若筛选后为空（理论上不会发生，中国神话有 100+ 篇），回退为不过滤，避免首页空白。
    var prefs = st.preferences || [];
    var activePrefs = prefs.filter(function(p){ return PREF_TAG_MAP[p]; });
    if (activePrefs.length) {
      var filtered = allPool.filter(function(s){
        var tags = s.tags || [];
        return activePrefs.some(function(p){
          return PREF_TAG_MAP[p].some(function(t){ return tags.indexOf(t) >= 0; });
        });
      });
      if (filtered.length) allPool = filtered;
    }
    // 排除「已读完」的故事（滚到底 或 音频播完），永不进每日推荐；
    // 已推荐但没读完的允许重复出现（不进排除集）。
    var rd=getReadDonePool();
    var avail=allPool.filter(function(s){ return !rd[s.id]; });
    if(!avail.length){
      // 极端情况：全部故事都读完了 → 重置「已读完」池，重新开始推荐
      rd={}; readDonePool=rd; saveReadDonePool(rd);
      avail=allPool.slice();
    }
    // 洗牌
    for(var i=avail.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var tmp=avail[i];avail[i]=avail[j];avail[j]=tmp;}
    var out=[]; var cult={};
    while(out.length<3 && avail.length){var s=avail.shift();
      if(out.length<2 && cult[s.culture]) continue;
      out.push(s); cult[s.culture]=true;
    }
    if(out.length<3){avail.forEach(function(s){if(out.length<3&&out.indexOf(s)<0)out.push(s);});}
    // 为每张卡片分配不重复的随机封面
    batchCovers={};
    var covers=pickCovers(out.length);
    out.forEach(function(s,i){batchCovers[s.id]=covers[i];});
    return out;
  }

  /* ================================================
   图书馆 / 首页 — 单卡片轮播式布局
   ================================================ */
  /* ========== 封面图池（11 张星橙 IP 3D 场景封面，随机不重复） ========== */
  var COVER_POOL = [
    'assets/covers/cover_01_campfire.jpg',     // 篝火+兔子
    'assets/covers/cover_02_ocean.jpg',        // 海底+水母
    'assets/covers/cover_03_moon_fishing.jpg', // 月亮垂钓
    'assets/covers/cover_04_mushroom.jpg',     // 蘑菇森林
    'assets/covers/cover_05_tea_party.jpg',    // 枫叶茶会
    'assets/covers/cover_06_paper_plane.jpg',  // 纸飞机云海
    'assets/covers/cover_07_flower_sleep.jpg', // 花朵里安睡
    'assets/covers/cover_08_garden_plant.jpg', // 种植园丁
    'assets/covers/cover_09_rainbow_paint.jpg',// 彩虹画笔
    'assets/covers/cover_10_ice_skate.jpg',    // 溜冰冬日
    'assets/covers/cover_11_harp_music.jpg'    // 星空竖琴
  ];
  /* 当前 batch 每张卡片的封面索引映射（storyId → coverPool index） */
  var batchCovers = {};

  function shuffleArray(arr){
    for(var i=arr.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var tmp=arr[i];arr[i]=arr[j];arr[j]=tmp;}
    return arr;
  }

  /* 从池中随机取 n 个不重复的封面路径 */
  function pickCovers(n){
    var indices = [];
    for(var i=0;i<COVER_POOL.length;i++) indices.push(i);
    shuffleArray(indices);
    return indices.slice(0, n).map(function(idx){ return COVER_POOL[idx]; });
  }

  /* 获取故事封面：优先 batch 分配，否则从池中随机取一张 */
  function getCoverImg(s){
    if(batchCovers[s.id]) return batchCovers[s.id];
    return COVER_POOL[Math.floor(Math.random()*COVER_POOL.length)];
  }

  /* 单张卡片内部 markup（不含外层 article） */
  function cardInner(s){
    return ''+
      /* 封面图区域（标签叠加在图片上） */
      '<div class="card-cover-wrap">'+
        '<button class="cover-heart" aria-label="收藏">'+heartSvg(Store.isFavorite(s.id))+'</button>'+
        '<img src="'+esc(getCoverImg(s))+'" alt="'+esc(s.title)+' 封面" class="card-cover-img" loading="lazy" decoding="async" />'+
        '<div class="cover-tags">'+
          tagPills([s.culture],'orange')+
          tagPills(s.tags.slice(0,2),'dark')+
        '</div>'+
      '</div>'+
      /* 信息体 */
      '<div class="card-body">'+
        '<h2 class="card-story-title">'+esc(s.title)+'</h2>'+
        '<p class="card-desc">'+esc(s.summary)+'</p>'+
        '<div class="card-meta-row">'+
          starRow(s.popularity)+
          '<span class="meta-duration">⏱ '+s.duration+' 分钟</span>'+
        '</div>'+
        '<button class="cta-btn" data-action="read">'+
          '▶ 开始阅读'+
        '</button>'+
      '</div>';
  }

  /* 堆叠卡片组：渲染 batch 中的全部故事（默认 3 张） */
  function deckCardsHtml(){
    return batch.map(function(s, idx){
      return '<article class="feature-card" data-idx="'+idx+'" data-id="'+s.id+'" data-pos="'+idx+'">'+
        cardInner(s)+
      '</article>';
    }).join('');
  }

  /* 根据 topIndex 更新每张卡的堆叠层级（不重建 DOM，CSS 过渡产生滑动效果） */
  function updateDeckPositions(){
    var len = batch.length;
    $$('#cardDeck .feature-card').forEach(function(c){
      var idx = +c.getAttribute('data-idx');
      var pos = ((idx - topIndex) % len + len) % len;
      c.setAttribute('data-pos', pos);
    });
  }

  /* 左/右滑动切换卡片 */
  var deckMouseUp = null; // 模块级，避免重复绑定累积
  function bindDeckSwipe(){
    var deck = $('#cardDeck'); if(!deck) return;
    var sx=0, sy=0, dragging=false;
    function down(x,y){ sx=x; sy=y; dragging=true; }
    function up(x,y){
      if(!dragging) return; dragging=false;
      var dx=x-sx, dy=y-sy;
      if(Math.abs(dx)>50 && Math.abs(dx)>Math.abs(dy)){
        if(dx<0) topIndex=(topIndex+1)%batch.length;       // 左滑 → 下一张
        else     topIndex=(topIndex-1+batch.length)%batch.length; // 右滑 → 上一张
        updateDeckPositions();
      }
    }
    deck.addEventListener('touchstart', function(e){ var t=e.touches[0]; down(t.clientX,t.clientY); }, {passive:true});
    deck.addEventListener('touchend',   function(e){ var t=e.changedTouches[0]; up(t.clientX,t.clientY); }, {passive:true});
    deck.addEventListener('mousedown',  function(e){ down(e.clientX,e.clientY); });
    if(deckMouseUp) document.removeEventListener('mouseup', deckMouseUp);
    deckMouseUp = function(e){ if(dragging) up(e.clientX,e.clientY); };
    document.addEventListener('mouseup', deckMouseUp);
  }

  /* 首页星空粒子（性能优化：已按用户要求关闭，不再生成上升粒子） */
  function initStarField(){
    return; // 动效已关闭，避免持续重绘
    var field = document.getElementById('starField');
    if(!field || field.dataset.init) return;
    field.dataset.init = '1';
    var N = 26, html = '';
    for(var i=0;i<N;i++){
      var size = (1.5 + Math.random()*2.4).toFixed(2);
      var left = (Math.random()*100).toFixed(2);
      var dur = (16 + Math.random()*16).toFixed(2);     // 缓慢：16~32s 一轮
      var delay = (-Math.random()*32).toFixed(2);        // 负延迟：加载即散布在各高度
      var o1 = (0.45 + Math.random()*0.45).toFixed(2);   // 高亮随机 .45~.90
      var o2 = (0.12 + Math.random()*0.30).toFixed(2);   // 眨眼低值 .12~.42
      var dx = ((Math.random()*40)-20).toFixed(1);       // 随机横向漂移 ±20px
      var warm = Math.random() < 0.3 ? ' warm' : '';
      html += '<span class="sp'+warm+'" style="left:'+left+'%;width:'+size+'px;height:'+size+'px;'+
              '--o1:'+o1+';--o2:'+o2+';--dx:'+dx+'px;'+
              'animation-duration:'+dur+'s;animation-delay:'+delay+'s;"></span>';
    }
    field.innerHTML = html;
  }

  function renderLibrary(){
    document.body.classList.remove('reader-open','view-vault','view-settings');
    document.body.classList.add('view-library');
    if(!batch.length){batch=pickBatch();}
    topIndex = 0;

    /* 数据未就绪时显示加载骨架屏 */
    if(!_storiesReady || !batch.length){
      var _loading = !_storiesReady && !_dataLoadFailed;
      var _msg;
      if(_dataLoadFailed){
        _msg = '⚠️ 故事数据未能加载<br/>'+
          '<span style="font-size:12px;opacity:.6">数据脚本（stories_data.js，约 2171KB）在设备上没有成功执行。'+
          '请：① 完全关闭 APP 后重新打开；② 仍不行则在「设置 → 清除缓存」后重启手机再试。</span>';
      }else if(_loading){
        _msg = '✦ 正在整理今晚的故事书架…<br/>'+
          '<span style="font-size:12px;opacity:.6">首次加载需解析 '+Math.round(2222899/1024)+'KB 故事数据</span>';
      }else{
        _msg = '⚠️ 故事数据为空<br/>'+
          '<span style="font-size:12px;opacity:.6">请重启 App，或在设置页清除缓存后重试</span>';
      }
      $app.innerHTML =
        '<header class="lib-header">'+
          '<div>'+
            '<p class="lib-greet">'+timeGreeting()+'</p>'+
            '<h1 class="lib-main-title">今晚读哪一个？</h1>'+
          '</div>'+
          '<img src="assets/ip_avatar.jpg" alt="星橙" class="lib-avatar-img" />'+
        '</header>'+
        '<div class="card-deck" style="min-height:360px;display:flex;align-items:center;justify-content:center">'+
          '<p style="color:var(--text-muted);font-size:14px;text-align:center;padding:20px">'+_msg+'</p>'+
        '</div>';
      return;
    }
    $app.innerHTML =
      '<header class="lib-header">'+
        '<div>'+
          '<p class="lib-greet">'+timeGreeting()+'</p>'+
          '<h1 class="lib-main-title">今晚读哪一个？</h1>'+
        '</div>'+
        '<img src="assets/ip_avatar.jpg" alt="星橙" class="lib-avatar-img" />'+
      '</header>'+

      /* 堆叠卡片组（3 张，左滑切换） */
      '<div class="card-deck" id="cardDeck">'+ deckCardsHtml() +'</div>'+

      /* 换一批 */
      '<div class="refresh-bar">'+
        '<button class="refresh-btn" id="refreshBtn">'+ICONS.refresh+' 换一批故事</button>'+
        '<p class="refresh-timer">今日推荐将在 <strong id="countdown">02:45:12</strong> 后更新</p>'+
      '</div>';

    /* 事件绑定即使出错也不应阻止卡片上屏：包一层 try/catch */
    try{ bindLibraryEvents(); }catch(e){ if(window.console) console.error('bindLibraryEvents failed', e); }
    try{ startCountdown(); }catch(e){ if(window.console) console.error('startCountdown failed', e); }
  }

  function heartSvg(on){
    return '<svg width="16" height="16" viewBox="0 0 24 24" fill="'+(on?'#ffc68b':'none')+'" stroke="'+(on?'#ffc68b':'#dac2ae')+'" stroke-width="1.8"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2l-2.81 6.63-7.19.61 5.46 4.73L6.82 21z"/></svg>';
  }

  function bindLibraryEvents(){
    /* 每张卡片的「开始阅读」与「收藏」——只有最前卡片（pos 0）可操作，点后方卡片则把它推到最前 */
    $$('#cardDeck .feature-card').forEach(function(card){
      var id=card.getAttribute('data-id');
      var idx=+card.getAttribute('data-idx');
      var cta=card.querySelector('.cta-btn');
      if(cta) cta.addEventListener('click',function(){
        if(card.getAttribute('data-pos')!=='0'){ topIndex=idx; updateDeckPositions(); return; }
        openReading(id);
      });
      var heart=card.querySelector('.cover-heart');
      if(heart) heart.addEventListener('click',function(e){
        e.stopPropagation();
        if(card.getAttribute('data-pos')!=='0'){ topIndex=idx; updateDeckPositions(); return; }
        var on=Store.toggleFavorite(id);
        this.innerHTML=heartSvg(on);
        toast(on?'已藏进星星里 ✦':'已取消收藏');
      });
    });
    /* 左/右滑切换堆叠卡片 */
    try{ bindDeckSwipe(); }catch(e){ if(window.console) console.error('bindDeckSwipe failed', e); }
    /* 换一批 */
    var _rb = $('#refreshBtn');
    if(_rb){
      _rb.addEventListener('click',function(){
        this.disabled=true;this.textContent='正在寻找今晚的新故事…';
        var self=this;
        setTimeout(function(){batch=pickBatch();topIndex=0;renderLibrary();},700);
      });
    }
  }

  /* 倒计时 */
  var countdownTimer=null;
  function startCountdown(){
    clearInterval(countdownTimer);
    var total=9912; // 2h45m12s in seconds
    countdownTimer=setInterval(function(){
      total=Math.max(0,total-1);
      var el=$('#countdown');
      if(el) el.textContent=formatTime(total);
    },1000);
  }
  function formatTime(sec){
    var h=Math.floor(sec/3600); var m=Math.floor((sec%3600)/60); var s=sec%60;
    return [h,m,s].map(function(v){return String(v).padStart(2,'0');}).join(':');
  }

  function timeGreeting(){
    var h=new Date().getHours();
    if(h<6) return '夜深了，小橙子';
    if(h<11) return '早上好，小橙子';
    if(h<14) return '中午好，小橙子';
    if(h<18) return '下午好，小橙子';
    return '晚上好，小橙子';
  }

  /* ================================================
   朗读页 — 沉浸式阅读 + 浮动播放器
   ================================================ */
  function splitSentences(text){
    var out=[],buf='';
    for(var i=0;i<text.length;i++){var ch=text[i];buf+=ch;
      if(/[。！？；]/.test(ch)){out.push(buf);buf='';}
      else if(ch==='\n'){if(buf.trim())out.push(buf);buf='';}
    }
    if(buf.trim())out.push(buf);return out;
  }

  function openReading(id){
    var s=find(id);if(!s)return;
    storyId=id; view='reading'; $nav.style.display='none';
    document.body.classList.add('reader-open');
    playerOpen=false;

    var st=Store.getSettings();
    var idx=0;
    var paras=s.content.split('\n').filter(function(p){return p.trim();});
    var body='';
    paras.forEach(function(p){
      var sens=splitSentences(p);
      body+='<p>'+sens.map(function(sent){
        var i=idx++;
        return '<span class="sentence" data-index="'+i+'">'+esc(sent)+'</span>';
      }).join('')+'</p>';
    });

    var fav=Store.isFavorite(id);
    var prog=Store.getProgress(id);
    var fontId=st.fontSize;
    var fCls='fs-'+(fontId==='small'?'sm':fontId==='standard'?'md':fontId==='large'?'lg':fontId==='xlarge'?'xl':fontId||'md');

    $app.innerHTML =
      '<div class="reader">'+
        /* 渐变装饰圆 */
        '<div class="reader-deco-l"></div><div class="reader-deco-r"></div>'+
        /* 内容区 */
        '<div class="reader-inner">'+
          /* 头部：返回（左上固定）+ 标题（单独一行·居中）+ 标签（单独一行·居中） */
          '<header class="reader-head">'+
            '<button class="reader-back" id="readerBack" aria-label="返回">←</button>'+
            '<div class="reader-head-main">'+
              '<h1 class="reader-title">'+esc(s.title)+'</h1>'+
              '<div class="reader-tags">'+
                tagPills(s.tags.slice(0,1),'dark')+
                tagPills(s.tags.slice(1),'orange')+
              '</div>'+
            '</div>'+
          '</header>'+
          /* 正文滚动区 */
          '<main class="reader-scroll" id="readerScroll">'+
            '<article class="reading-body '+fCls+'" id="readingBody">'+body+'</article>'+
            /* 底部收藏按钮 + 返回图书馆按钮 */
            '<div class="reader-fav-bar" id="readerFavBar">'+
              '<button class="reader-home-btn" id="readerHomeBtn">'+ICONS.home+' 返回图书馆</button>'+
              '<button class="reader-fav-btn" id="readerFavBtn">'+(fav?'★ 已藏进星星里 ✦':'☆ 藏进星星里')+'</button>'+
            '</div>'+
          '</main>'+
        '</div>';

    bindReaderEvents(id);

    /* 进入即阅读模式：显式保证标题为柔白（无选中色），不依赖任何状态回调时序，杜绝上一则后台朗读泄漏导致的“一进去就橙” */
    setReaderTitlePlaying(false);

    // 恢复进度
    if(prog.percent>0){
      var sc=$('#readerScroll');
      requestAnimationFrame(function(){
        sc.scrollTop=(sc.scrollHeight-sc.clientHeight)*(prog.percent/100);
      });
    }
  }

  function bindReaderEvents(id){
    /* 返回按钮（左上角） */
    $('#readerBack').addEventListener('click',function(){ goBackFromReader(); });

    /* 阅读完成后底部「返回图书馆」按钮 */
    var rHome=$('#readerHomeBtn');
    if(rHome) rHome.addEventListener('click',function(){ goBackFromReader(); });

    /* 滚动记录进度（文字阅读，无语音） */
    var sc=$('#readerScroll'), saveTimer=null;
    sc.addEventListener('scroll',function(){
      var max=sc.scrollHeight-sc.clientHeight;
      var pct=max?(sc.scrollTop/max)*100:100;
      if(pct>=98) markReadDone(id);   // 详情滚到底 → 判定已读完
      clearTimeout(saveTimer);
      saveTimer=setTimeout(function(){
        Store.setProgress(id,pct);
        Store.markRead(id);
      },400);
    });

    /* 收藏 —— 点击标题区域触发 */
    $('.reader-title').addEventListener('click',function(){
      var on=Store.toggleFavorite(id);
      toast(on?'已藏进星星里 ✦':'已取消收藏');
      updateReaderFavBtn(id);
    });
    /* 收藏 —— 底部收藏按钮 */
    var rfb=$('#readerFavBtn');
    if(rfb) rfb.addEventListener('click',function(){
      var on=Store.toggleFavorite(id);
      updateReaderFavBtn(id);
      toast(on?'已藏进星星里 ✦':'已取消收藏');
    });
  }

  /* 标题颜色随阅读高亮（已移除语音朗读，仅保留标题柔白态） */
  function setReaderTitlePlaying(on){
    var t=$('.reader-title'); if(t) t.classList.toggle('is-playing', !!on);
  }
  /* 更新阅读页底部收藏按钮状态 */
  function updateReaderFavBtn(storyId){
    var btn=$('#readerFavBtn');
    if(!btn) return;
    var on=Store.isFavorite(storyId);
    btn.textContent=on?'★ 已藏进星星里 ✦':'☆ 藏进星星里';
    btn.classList.toggle('favorited', on);
  }

  /* 从朗读页返回图书馆 */
  function goBackFromReader(){
    view='library';$nav.style.display='';batch=pickBatch();topIndex=0;
    renderLibrary();
  }


  /* ================================================
   星藏阁 — Tab 切换 + 封面卡片列表
   ================================================ */
  function renderVault(){
    document.body.classList.remove('reader-open','view-library','view-settings');
    document.body.classList.add('view-vault');
    view='vault';$nav.style.display='';
    var favs=Store.getFavorites(stories);
    var hist=Store.getHistory(stories);

    // 为星藏阁卡片分配不重复封面
    var vCovers=pickCovers(Math.max(favs.length, hist.length));
    var vi=0;
    batchCovers={};
    (vaultTab==='fav'?favs:hist).forEach(function(s,i){
      if(i<vCovers.length) batchCovers[s.id]=vCovers[i];
    });

    var tabs=
      '<div class="vault-tabs">'+
        '<button class="vtab'+(vaultTab==='fav'?' active':'')+'" data-t="fav">我的收藏</button>'+
        '<button class="vtab'+(vaultTab==='hist'?' active':'')+'" data-t="hist">历史记录</button>'+
      '</div>';

    var list='',empty='';
    if(vaultTab==='fav'){
      if(!favs.length){
        empty='<div class="empty-state">'+
          '<img src="assets/vault_empty_fav.jpg" alt="" class="empty-whale" />'+
          '<p class="empty-title">还没有收藏的故事</p>'+
          '<p class="empty-sub">遇到喜欢的故事，就把它藏进星星里吧 ✦</p>'+
        '</div>';
      }else{
        list=favs.map(function(s){return vaultCard(s,'fav');}).join('');
      }
    }else{
      if(!hist.length){
        empty='<div class="empty-state">'+
          '<img src="assets/ip_whale.jpg" alt="" class="empty-whale" />'+
          '<p class="empty-title">还没有阅读记录</p>'+
          '<p class="empty-sub">翻开一篇故事，星橙会记住你的足迹 🌙</p>'+
        '</div>';
      }else{
        list=hist.map(function(s){return vaultCard(s,'hist');}).join('');
      }
    }

    $app.innerHTML =
      '<header class="vault-head">'+
        '<img src="assets/vault_header.jpg" alt="星藏阁" class="vault-hero-img" />'+
      '</header>'+
      tabs+
      (list ? '<div class="vault-list">'+list+'</div>' : empty);

    // Tab 切换
    $$('.vtab').forEach(function(t){
      t.addEventListener('click',function(){vaultTab=t.getAttribute('data-t');renderVault();});
    });
    // 卡片点击
    $$('.vcard').forEach(function(c){
      c.addEventListener('click',function(){openReading(c.getAttribute('data-id'));});
    });
    // 封面上收藏（与首页统一）
    $$('.vcard .cover-heart').forEach(function(b){
      b.addEventListener('click',function(e){
        e.stopPropagation();var id=this.closest('.vcard').getAttribute('data-id');
        var on=Store.toggleFavorite(id);
        this.innerHTML=heartSvg(on);
        toast(on?'已藏进星星里 ✦':'已取消收藏');
        // 在「我的收藏」标签下取消收藏，卡片应立即从列表消失
        if(!on && vaultTab==='fav'){ renderVault(); }
      });
    });
  }

  /* 星藏阁卡片 */
  function vaultCard(s,type){
    var prog=Store.getProgress(s.id); var pct=Math.round(prog.percent||0);
    var badge=s.tags.indexOf('有声')>=0?'🔊 有声故事':s.popularity>=4?'⭐ 必读经典':'经典故事';
    return '<article class="vcard" data-id="'+s.id+'">'+
      '<div class="vcard-cover">'+
        '<img src="'+esc(getCoverImg(s))+'" alt="'+esc(s.title)+' 封面" class="vcard-cover-img" />'+
        '<span class="vcard-badge">'+badge+'</span>'+
        '<button class="cover-heart" aria-label="收藏">'+heartSvg(Store.isFavorite(s.id))+'</button>'+
      '</div>'+
      '<div class="vcard-body">'+
        '<h3 class="vcard-title">'+esc(s.title)+
        '</h3>'+
        '<p class="vcard-desc">'+esc(s.summary)+'</p>'+
        '<div class="vcard-prog">'+
          '<div class="vprog-bar"><div class="vprog-fill" style="width:'+pct+'%"></div></div>'+
          '<span class="vprog-pct">已读 '+pct+'%</span>'+
        '</div>'+
      '</div>'+
    '</article>';
  }


  /* ================================================
   设置 — 分区卡片式布局
   ================================================ */
  function renderSettings(){
    document.body.classList.remove('reader-open','view-library','view-vault');
    document.body.classList.add('view-settings');
    view='settings';$nav.style.display='';
    var st=Store.getSettings();

    // 年龄 chips
    var ageHtml=AGES.map(function(a){
      var sel=st.age>=a.min&&st.age<=a.max;
      return '<button class="age-chip'+(sel?' selected':'')+'" data-a-min="'+a.min+'" data-a-max="'+a.max+'">'+a.label+'</button>';
    }).join('');

    // 偏好网格
    var prefHtml=PREFS.map(function(p){
      var on=st.preferences.indexOf(p)>=0;
      var icon=prefIcon(p);
      var extra = (p==='王尔德' || p==='安徒生') ? ' wide' : '';
      return '<div class="pref-card'+(on?' selected':'')+extra+'" data-pref="'+esc(p)+'">'+icon+'<span>'+esc(p)+'</span></div>';
    }).join('');

    $app.innerHTML =
      '<div class="settings-page">'+
        '<header class="set-head">'+
          '<h1>设置</h1>'+
          '<p class="set-head-sub">开启您的专属奇幻阅读之旅。</p>'+
        '</header>'+

        /* 阅读年龄 */
        secBox('moon','阅读年龄',
          '<div class="age-chips">'+ageHtml+'</div>')+

        /* 兴趣偏好 */
        secBox('sparkle','兴趣偏好',
          '<div class="pref-grid">'+prefHtml+'</div>')+

        /* 界面显示 */
        secBox('display','界面显示',
          '<div class="slider-group"><label>页面亮度</label>'+
            '<input type="range" id="setBrightBar" min="0.3" max="1.2" step="0.05" value="'+st.brightness+'"/>'+
            '<span class="slider-val" id="setBrightVal">'+Math.round(st.brightness*100)+'%</span></div>')+

        /* 存储空间 */
        secBox('storage','存储空间',
          '<div class="storage-row">'+
            '<div><span class="set-row-label">离线阅读缓存</span><span class="cache-info">已占用 124 MB</span></div>'+
            '<button class="clear-btn" id="clearCacheBtn">清理缓存</button>'+
          '</div>')+

        /* 底部晚安 */
        '<div class="set-footer">'+
          '<img src="assets/reading_hero.jpg" alt="星橙" class="set-footer-img" />'+
          '<p class="set-footer-quote">"一切都为你准备好了，"<br>做个好梦吧</p>'+
        '</div>'+
      '</div>';

    bindSettingsEvents();
  }

  function secBox(icon,title,body){
    return '<div class="set-section">'+
      '<h2 class="set-section-title">'+(ICONS[icon]||'')+'<span>'+title+'</span></h2>'+
      body+
    '</div>';
  }

  function toggleRow(label,id,on){
    return '<div class="toggle-row">'+
      '<span class="toggle-label">'+label+'</span>'+
      '<label class="toggle-switch">'+
        '<input type="checkbox" id="'+id+'"'+(on?' checked':'')+'/>'+
        '<span class="toggle-slider"></span>'+
      '</label>'+
    '</div>';
  }

  function prefIcon(name){
    var map={
      '奇幻冒险':'castle','童话寓言':'bookStroke','自然百科':'leaf','科幻未来':'rocket',
      '中国神话':'myth','历史趣事':'history',
      '王尔德':'bookStroke','安徒生':'bookStroke'
    };
    return ICONS[map[name]||'bookStroke']||'';
  }

  function bindSettingsEvents(){
    // 年龄选择
    $$('.age-chip').forEach(function(c){
      c.addEventListener('click',function(){
        var min=+this.getAttribute('data-a-min');var max=+this.getAttribute('data-a-max');
        Store.updateSettings({age:(min+max)/2});
        $$('.age-chip').forEach(function(x){x.classList.toggle('selected',x===this);}.bind(this));
        toast('年龄已更新');
      });
    });
    // 偏好选择
    $$('.pref-card').forEach(function(c){
      c.addEventListener('click',function(){
        var p=this.getAttribute('data-pref');
        Store.togglePreference(p);
        this.classList.toggle('selected');
      });
    });
    // 亮度滑块
    $('#setBrightBar').addEventListener('input',function(){
      var v=+this.value;
      $('#setBrightVal').textContent=Math.round(v*100)+'%';
      Store.updateSettings({brightness:v});
      applyBrightness();
    });
    // 清理缓存
    $('#clearCacheBtn').addEventListener('click',function(){
      if(confirm('确定清理缓存吗？已收藏的故事会保留。')){
        Store.clearCache();toast('缓存已清理 ✦');
      }
    });
  }


  /* ---------- 全局样式应用 ---------- */
  function applyReadingStyle(){
    var st=Store.getSettings();
    var cls='md';
    if(st.fontSize==='sm'||st.fontSize==='lg'||st.fontSize==='xl') cls=st.fontSize;
    else if(st.fontSize==='small') cls='sm';
    else if(st.fontSize==='standard') cls='md';
    else if(st.fontSize==='large') cls='lg';
    else if(st.fontSize==='xlarge') cls='xl';
    var b=$$('#readingBody'); b.forEach(function(el){ el.className='reading-body fs-'+cls; });
  }
  function applyBrightness(){
    var st=Store.getSettings();
    document.documentElement.style.setProperty('--brightness',st.brightness);
  }

  /* ---------- 底部导航 ---------- */
  function initNav(){
    $$('#bottomNav .nav-tab').forEach(function(item){
      item.addEventListener('click',function(){
        var tgt=item.getAttribute('data-view');
        if(view==='reading'){$nav.style.display='';}
        setNavActive(tgt);
        if(tgt==='library'){batch=pickBatch();topIndex=0;renderLibrary();}
        else if(tgt==='vault'){renderVault();}
        else if(tgt==='settings'){renderSettings();}
      });
    });
  }
  function setNavActive(tgt){
    $$('#bottomNav .nav-tab').forEach(function(i){
      i.classList.toggle('active',i.getAttribute('data-view')===tgt);
    });
  }

  /* ---------- 启动入口 ---------- */
  function init(){
    initStarField();
    applyBrightness();initNav();setNavActive('library');
    /* 立即渲染 UI（此时 stories 可能为空，pickBatch 会返回空数组，
       renderLibrary 渲染空骨架；_initStories 异步完成后会重新 renderLibrary）*/
    renderLibrary();
  }

  document.addEventListener('DOMContentLoaded',init);
})();
