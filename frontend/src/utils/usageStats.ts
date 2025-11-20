const STORAGE_KEY = "beancount_usage_stats";
const RECENT_DAYS = 30; // 只统计最近30天的使用记录
const DEFAULT_RECENT_LIMIT = 3; // 返回最近最常用的3个

interface UsageRecord {
  timestamps: number[]; // 所有使用时间戳
}

interface UsageStats {
  accounts: Record<string, UsageRecord>;
  categories: Record<string, UsageRecord>;
}

const getStats = (): UsageStats => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // 兼容旧版本数据格式
      if (parsed.accounts && typeof parsed.accounts === "object") {
        // 检查是否是旧格式（简单的计数）
        const firstAccountKey = Object.keys(parsed.accounts)[0];
        if (firstAccountKey && typeof parsed.accounts[firstAccountKey] === "number") {
          // 旧格式，需要迁移
          return {
            accounts: {},
            categories: {},
          };
        }
      }
      return {
        accounts: parsed.accounts || {},
        categories: parsed.categories || {},
      };
    }
  } catch (e) {
    console.error("Failed to load usage stats", e);
  }
  return {
    accounts: {},
    categories: {},
  };
};

const saveStats = (stats: UsageStats) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stats));
  } catch (e) {
    console.error("Failed to save usage stats", e);
  }
};

export const recordAccountUsage = (accountName: string) => {
  if (!accountName) return;
  const stats = getStats();
  
  if (!stats.accounts[accountName]) {
    stats.accounts[accountName] = { timestamps: [] };
  }
  
  // 添加当前时间戳
  stats.accounts[accountName].timestamps.push(Date.now());
  
  // 清理过期的时间戳（超过30天）
  const cutoffTime = Date.now() - RECENT_DAYS * 24 * 60 * 60 * 1000;
  stats.accounts[accountName].timestamps = stats.accounts[accountName].timestamps.filter(
    (ts) => ts > cutoffTime
  );
  
  saveStats(stats);
};

export const recordCategoryUsage = (categoryName: string) => {
  if (!categoryName) return;
  const stats = getStats();
  
  if (!stats.categories[categoryName]) {
    stats.categories[categoryName] = { timestamps: [] };
  }
  
  // 添加当前时间戳
  stats.categories[categoryName].timestamps.push(Date.now());
  
  // 清理过期的时间戳（超过30天）
  const cutoffTime = Date.now() - RECENT_DAYS * 24 * 60 * 60 * 1000;
  stats.categories[categoryName].timestamps = stats.categories[categoryName].timestamps.filter(
    (ts) => ts > cutoffTime
  );
  
  saveStats(stats);
};

// 获取最近30天内使用频率最高的项目
const getRecentTopItems = (
  records: Record<string, UsageRecord>,
  limit: number
): string[] => {
  const cutoffTime = Date.now() - RECENT_DAYS * 24 * 60 * 60 * 1000;
  
  // 计算每个项目在最近30天内的使用次数
  const recentCounts: Record<string, { count: number; lastUsed: number }> = {};
  
  Object.entries(records).forEach(([name, record]) => {
    const recentTimestamps = record.timestamps.filter((ts) => ts > cutoffTime);
    if (recentTimestamps.length > 0) {
      recentCounts[name] = {
        count: recentTimestamps.length,
        lastUsed: Math.max(...recentTimestamps),
      };
    }
  });
  
  // 按使用次数（主要）和最后使用时间（次要）排序
  return Object.keys(recentCounts)
    .sort((a, b) => {
      const countDiff = recentCounts[b].count - recentCounts[a].count;
      if (countDiff !== 0) return countDiff;
      return recentCounts[b].lastUsed - recentCounts[a].lastUsed;
    })
    .slice(0, limit);
};

export const getFrequentlyUsedAccounts = (limit: number = DEFAULT_RECENT_LIMIT): string[] => {
  const stats = getStats();
  return getRecentTopItems(stats.accounts, limit);
};

export const getFrequentlyUsedCategories = (limit: number = DEFAULT_RECENT_LIMIT): string[] => {
  const stats = getStats();
  return getRecentTopItems(stats.categories, limit);
};
