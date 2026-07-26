/**
 * 星橙故事铺 - 本地存储模块
 * 负责收藏、阅读进度、设置、阅读记录的持久化。
 * 所有数据存于 localStorage（应用私有存储，原型阶段使用浏览器 localStorage 模拟）。
 */
(function () {
  'use strict';

  var KEY = 'xinge_story_data_v1';

  var DEFAULT_SETTINGS = {
    // V18: 已删除「阅读年龄」。偏好 = 书名，选中即开启对应书籍，支持多选，默认全开。
    preferences: ['安徒生','王尔德','中国童话','成语故事','格林童话（果麦版）','历史传奇','意大利童话'],
    voice: 'zh-CN-XiaoxiaoNeural', // V19: Edge 免费神经语音音色 id（晓晓·温柔女声·推荐）
    speed: 'normal', // V19: 朗读语速：slow(慢 -18%) / normal(常 -10%) / fast(快 +12%)
    fontSize: 'md', // 阅读字号：sm / md / lg / xl（默认标准，设置页不再提供调节）
    lineHeight: 'comfort', // 行距：compact / comfort / loose
    brightness: 1.0, // 页面亮度 0-1（默认全亮，用户可在设置里调暗）
    autoDownload: true // 自动下载开关
  };

  var DEFAULT_STATE = {
    favorites: {}, // { [storyId]: { favoritedAt: timestamp } }
    progress: {}, // { [storyId]: { percent: 0-100, lastSentence: 0, updatedAt } }
    history: {}, // { [storyId]: { lastReadAt } } 阅读记录
    settings: DEFAULT_SETTINGS
  };

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return clone(DEFAULT_STATE);
      var parsed = JSON.parse(raw);
      // 合并默认设置，兼容旧数据
      parsed.settings = Object.assign(clone(DEFAULT_SETTINGS), parsed.settings || {});
      // 数据迁移：旧版把亮度默认存成 0.6（整体压暗，像蒙了层黑罩），
      // 升级到全亮，避免历史 localStorage 残留暗值覆盖新默认。
      // 仅当亮度处于明显偏暗区间（<=0.8）才重置，用户主动调暗的 0.8~1.2 不受影响。
      if (parsed.settings.brightness && parsed.settings.brightness <= 0.8) {
        parsed.settings.brightness = 1.0;
      }
      parsed.favorites = parsed.favorites || {};
      parsed.progress = parsed.progress || {};
      parsed.history = parsed.history || {};
      return parsed;
    } catch (e) {
      console.warn('读取本地数据失败，使用默认数据', e);
      return clone(DEFAULT_STATE);
    }
  }

  function clone(o) {
    return JSON.parse(JSON.stringify(o));
  }

  var state = load();

  function persist() {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
    } catch (e) {
      console.warn('保存本地数据失败', e);
    }
  }

  var Store = {
    // ---- 收藏 ----
    isFavorite: function (id) {
      return !!state.favorites[id];
    },
    toggleFavorite: function (id) {
      if (state.favorites[id]) {
        delete state.favorites[id];
      } else {
        state.favorites[id] = { favoritedAt: Date.now() };
      }
      persist();
      return this.isFavorite(id);
    },
    getFavorites: function (allStories) {
      return allStories.filter(function (s) {
        return !!state.favorites[s.id];
      });
    },

    // ---- 阅读进度 ----
    getProgress: function (id) {
      return state.progress[id] || { percent: 0, lastSentence: 0, updatedAt: 0 };
    },
    setProgress: function (id, percent, lastSentence) {
      state.progress[id] = {
        percent: Math.max(0, Math.min(100, Math.round(percent))),
        lastSentence: lastSentence || 0,
        updatedAt: Date.now()
      };
      persist();
    },
    isRead: function (id) {
      var p = state.progress[id];
      return !!(p && p.percent >= 95);
    },

    // ---- 阅读记录 ----
    markRead: function (id) {
      state.history[id] = { lastReadAt: Date.now() };
      persist();
    },
    getHistory: function (allStories) {
      return allStories.filter(function (s) {
        return !!state.history[s.id];
      });
    },

    // ---- 设置 ----
    getSettings: function () {
      return state.settings;
    },
    updateSettings: function (patch) {
      state.settings = Object.assign(state.settings, patch);
      persist();
      return state.settings;
    },
    togglePreference: function (tag) {
      var prefs = state.settings.preferences;
      var idx = prefs.indexOf(tag);
      if (idx >= 0) prefs.splice(idx, 1);
      else prefs.push(tag);
      persist();
      return state.settings.preferences;
    },

    // ---- 缓存清理（原型：仅清理进度/记录，保留收藏） ----
    clearCache: function () {
      // 依据 PRD：清理缓存不删除收藏故事
      state.progress = {};
      state.history = {};
      persist();
    },

    resetAll: function () {
      state = clone(DEFAULT_STATE);
      persist();
    }
  };

  window.Store = Store;
})();
