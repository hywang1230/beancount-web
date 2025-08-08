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
      // Performance metric not found
      return;
    }

    metric.endTime = performance.now();
    metric.duration = metric.endTime - metric.startTime;

    // Performance monitoring disabled in production

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

    // Performance report generation disabled
  }
}

export const perfMonitor = new PerformanceMonitor();

// 常用的性能装饰器
export function measurePerformance(name: string) {
  return function (
    _target: any,
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
        // Low FPS detected: ${fps}
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
