/**
 * 星橙故事铺 - 故事内容库
 * 说明：基础故事库已清空。所有故事均来自真实公版资源（Project Gutenberg）英文原典，
 * 经 AI 翻译为中文后注入 js/stories_data.js（window.STORY_LIBRARY_EXT），零编造。
 * 本文件仅保留设置页所需的标签与音色预设。字段遵循 PRD「故事字段」规范。
 */
window.STORY_LIBRARY = [];

/**
 * 设置页「故事偏好」可选标签（取自 PRD）
 */
window.PREFERENCE_TAGS = ['奇幻', '寓言', '冒险', '现实', '友情', '家庭', '传统民谚', '轻松幽默', '成长', '讽刺'];

/**
 * 三种预设音色（展示名 + 定位描述，不使用技术音色编号）
 */
window.VOICE_PROFILES = [
  { id: 'mom', name: '温柔妈妈音', desc: '温柔、舒缓，适合睡前' },
  { id: 'sister', name: '温暖姐姐音', desc: '亲切、轻快，富有陪伴感' },
  { id: 'story', name: '阳光故事音', desc: '明亮、清晰，适合冒险和寓言' },
  { id: 'night', name: '深夜星光音', desc: '低柔、空灵，伴你入眠' }
];
