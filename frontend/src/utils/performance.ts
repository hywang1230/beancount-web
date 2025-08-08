// 性能监控工具
interface PerformanceMetrics {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
}

class PerformanceMonitor {
  private metrics: Map<string, PerformanceMetrics> = new Map();
  private enabled: boolean;

  constructor() {
    this.enabled =
      (import.meta as any).env.DEV ||
      (import.meta as any).env.VITE_ENABLE_PERF_MONITOR === "true";
  }

  start(name: string): void {
    if (!this.enabled) return;

    this.metrics.set(name, {
      name,
      startTime: performance.now(),
    });
  }

  end(name: string): number | undefined {
    if (!this.enabled) return;

    const metric = this.metrics.get(name);
    if (!metric) {
      console.warn(`Performance metric "${name}" not found`);
      return;
    }

    metric.endTime = performance.now();
    metric.duration = metric.endTime - metric.startTime;

    if (this.enabled && metric.duration > 100) {
      console.warn(
        `⚠️ Performance: "${name}" took ${metric.duration.toFixed(2)}ms`
      );
    }

    return metric.duration;
  }

  measure(name: string, fn: () => any): any {
    if (!this.enabled) return fn();

    this.start(name);
    const result = fn();
    this.end(name);
    return result;
  }

  async measureAsync(name: string, fn: () => Promise<any>): Promise<any> {
    if (!this.enabled) return fn();

    this.start(name);
    const result = await fn();
    this.end(name);
    return result;
  }

  getMetrics(): PerformanceMetrics[] {
    return Array.from(this.metrics.values()).filter(
      (m) => m.duration !== undefined
    );
  }

  clear(): void {
    this.metrics.clear();
  }

  report(): void {
    if (!this.enabled) return;

    const metrics = this.getMetrics();
    if (metrics.length === 0) return;

    console.group("📊 Performance Report");
    metrics
      .sort((a, b) => (b.duration || 0) - (a.duration || 0))
      .forEach((metric) => {
        const duration = metric.duration!.toFixed(2);
        const emoji =
          metric.duration! > 500 ? "🔴" : metric.duration! > 100 ? "🟡" : "🟢";
        console.log(`${emoji} ${metric.name}: ${duration}ms`);
      });
    console.groupEnd();
  }
}

export const perfMonitor = new PerformanceMonitor();

// 常用的性能装饰器
export function measurePerformance(name: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = function (...args: any[]) {
      return perfMonitor.measure(`${name || propertyKey}`, () =>
        originalMethod.apply(this, args)
      );
    };

    return descriptor;
  };
}

// 内存使用监控
export function checkMemoryUsage(): void {
  if (!(import.meta as any).env.DEV) return;

  if ("memory" in performance) {
    const memory = (performance as any).memory;
    const used = Math.round((memory.usedJSHeapSize / 1048576) * 100) / 100;
    const total = Math.round((memory.totalJSHeapSize / 1048576) * 100) / 100;
    const limit = Math.round((memory.jsHeapSizeLimit / 1048576) * 100) / 100;

    if (used / total > 0.9) {
      console.warn(
        `🚨 Memory usage high: ${used}MB / ${total}MB (limit: ${limit}MB)`
      );
    } else {
      console.log(`💾 Memory usage: ${used}MB / ${total}MB`);
    }
  }
}

// 帧率监控
export function startFPSMonitor(): () => void {
  if (!(import.meta as any).env.DEV) return () => {};

  let frames = 0;
  let lastTime = performance.now();
  let isRunning = true;

  function tick() {
    if (!isRunning) return;

    frames++;
    const currentTime = performance.now();

    if (currentTime >= lastTime + 1000) {
      const fps = Math.round((frames * 1000) / (currentTime - lastTime));

      if (fps < 30) {
        console.warn(`🎭 Low FPS detected: ${fps}`);
      }

      frames = 0;
      lastTime = currentTime;
    }

    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);

  return () => {
    isRunning = false;
  };
}
