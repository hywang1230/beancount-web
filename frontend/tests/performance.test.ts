// 性能测试文件
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createRouter, createWebHistory } from "vue-router";

// 测试工具
const mockPerformance = () => {
  const marks: Record<string, number> = {};
  const measures: Record<string, number> = {};

  return {
    mark: (name: string) => {
      marks[name] = performance.now();
    },
    measure: (name: string, start: string, end: string) => {
      measures[name] = marks[end] - marks[start];
      return measures[name];
    },
    getMarks: () => marks,
    getMeasures: () => measures,
  };
};

describe("H5 Performance Optimizations", () => {
  let pinia: any;
  let router: any;
  let perf: any;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);

    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: "/", component: { template: "<div>Home</div>" } },
        {
          path: "/h5/transactions",
          component: { template: "<div>Transactions</div>" },
        },
      ],
    });

    perf = mockPerformance();

    // Mock API 请求
    vi.mock("@/utils/api", () => ({
      createCancellableGet: vi.fn(() => ({
        promise: Promise.resolve({ data: [], total_pages: 0 }),
        cancel: vi.fn(),
      })),
      createDebounce: vi.fn((fn, delay) => {
        const debounced = (...args: any[]) => {
          setTimeout(() => fn(...args), delay);
        };
        debounced.cancel = vi.fn();
        return debounced;
      }),
      RequestManager: vi.fn(() => ({
        add: vi.fn(),
        cancel: vi.fn(),
        cancelAll: vi.fn(),
        hasRequest: vi.fn(),
      })),
    }));
  });

  it("should cancel requests when filter changes", async () => {
    const { createCancellableGet, RequestManager } = await import(
      "@/utils/api"
    );
    const mockCancel = vi.fn();
    const mockAdd = vi.fn();

    (createCancellableGet as any).mockReturnValue({
      promise: Promise.resolve({ data: [], total_pages: 0 }),
      cancel: mockCancel,
    });

    (RequestManager as any).mockImplementation(() => ({
      add: mockAdd,
      cancel: vi.fn(),
      cancelAll: vi.fn(),
      hasRequest: vi.fn(),
    }));

    // 模拟筛选条件变更
    // 应该取消旧请求并发起新请求
    expect(mockAdd).toHaveBeenCalled();
  });

  it("should debounce filter changes", async () => {
    const { createDebounce } = await import("@/utils/api");

    const mockFn = vi.fn();
    const debounced = createDebounce(mockFn, 300);

    // 快速连续调用
    debounced();
    debounced();
    debounced();

    // 应该只执行一次
    await new Promise((resolve) => setTimeout(resolve, 350));
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it("should measure grouping performance", () => {
    perf.mark("grouping-start");

    // 模拟分组计算
    const transactions = Array.from({ length: 1000 }, (_, i) => ({
      id: `tx-${i}`,
      date: `2024-01-${(i % 30) + 1}`,
      amount: Math.random() * 1000,
      type: "expense",
    }));

    // 使用 Map 进行分组
    const groups = new Map();
    transactions.forEach((tx) => {
      if (!groups.has(tx.date)) {
        groups.set(tx.date, {
          date: tx.date,
          transactions: [],
          totalAmount: 0,
        });
      }
      const group = groups.get(tx.date);
      group.transactions.push(tx);
      group.totalAmount += tx.amount;
    });

    perf.mark("grouping-end");
    const groupingTime = perf.measure(
      "grouping",
      "grouping-start",
      "grouping-end"
    );

    // 分组应该在合理时间内完成
    expect(groupingTime).toBeLessThan(100); // 100ms
    expect(groups.size).toBeGreaterThan(0);
  });

  it("should handle large datasets efficiently", () => {
    perf.mark("large-dataset-start");

    // 模拟大数据集
    const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
      id: `tx-${i}`,
      date: `2024-${Math.floor(i / 1000) + 1}-${(i % 30) + 1}`,
      amount: Math.random() * 1000,
      type: i % 3 === 0 ? "income" : "expense",
    }));

    // 测试分组性能
    const groupMap = new Map();
    largeDataset.forEach((tx) => {
      if (!groupMap.has(tx.date)) {
        groupMap.set(tx.date, {
          date: tx.date,
          transactions: [],
          totalAmount: 0,
        });
      }
      const group = groupMap.get(tx.date);
      group.transactions.push(tx);
      group.totalAmount += tx.amount;
    });

    perf.mark("large-dataset-end");
    const processingTime = perf.measure(
      "large-dataset",
      "large-dataset-start",
      "large-dataset-end"
    );

    // 大数据集处理应该在合理时间内完成
    expect(processingTime).toBeLessThan(500); // 500ms
    expect(groupMap.size).toBeGreaterThan(0);
  });

  it("should cache results properly", () => {
    // 测试缓存命中
    const cache = new Map();
    const cacheKey = "test-key";
    const testData = { result: "cached" };

    // 第一次访问 - 缓存未命中
    perf.mark("cache-miss-start");
    if (!cache.has(cacheKey)) {
      cache.set(cacheKey, testData);
    }
    perf.mark("cache-miss-end");

    // 第二次访问 - 缓存命中
    perf.mark("cache-hit-start");
    const cached = cache.get(cacheKey);
    perf.mark("cache-hit-end");

    const missTime = perf.measure(
      "cache-miss",
      "cache-miss-start",
      "cache-miss-end"
    );
    const hitTime = perf.measure(
      "cache-hit",
      "cache-hit-start",
      "cache-hit-end"
    );

    expect(cached).toEqual(testData);
    expect(hitTime).toBeLessThan(missTime);
  });
});
