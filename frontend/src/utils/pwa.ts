/**
 * PWA相关工具函数
 */

/**
 * 检测是否运行在PWA模式下
 */
export function isPWAMode(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (window.navigator as any).standalone === true ||
    document.referrer.includes("android-app://")
  );
}

/**
 * 检测是否为iOS设备
 */
export function isIOS(): boolean {
  return /iPad|iPhone|iPod/.test(navigator.userAgent);
}

/**
 * 检测是否为安卓设备
 */
export function isAndroid(): boolean {
  return /Android/.test(navigator.userAgent);
}

/**
 * 获取安全区域高度
 */
export function getSafeAreaInsetBottom(): number {
  if (
    typeof CSS !== "undefined" &&
    CSS.supports("padding-bottom", "env(safe-area-inset-bottom)")
  ) {
    const computed = getComputedStyle(document.documentElement);
    const safeAreaBottom =
      computed.getPropertyValue("env(safe-area-inset-bottom)") || "0px";
    return parseInt(safeAreaBottom.replace("px", "")) || 0;
  }
  return 0;
}

/**
 * 计算PWA模式下底部按钮的最佳位置
 */
export function calculateBottomButtonPosition(): string {
  const baseTabBarHeight = 60; // 底部导航栏基础高度
  const safeAreaBottom = getSafeAreaInsetBottom();
  const isPWA = isPWAMode();
  const iOS = isIOS();

  if (isPWA) {
    if (iOS) {
      // iOS PWA模式需要额外的间距
      return `calc(${baseTabBarHeight + 10}px + env(safe-area-inset-bottom, ${
        safeAreaBottom + 5
      }px))`;
    } else {
      // Android PWA模式
      return `calc(${
        baseTabBarHeight + 5
      }px + env(safe-area-inset-bottom, ${safeAreaBottom}px))`;
    }
  }

  // 普通浏览器模式
  return `calc(${baseTabBarHeight}px + env(safe-area-inset-bottom, ${safeAreaBottom}px))`;
}

/**
 * 动态应用PWA样式
 */
export function applyPWAStyles(): void {
  const isPWA = isPWAMode();
  const iOS = isIOS();

  if (isPWA) {
    document.documentElement.classList.add("pwa-mode");

    if (iOS) {
      document.documentElement.classList.add("pwa-ios");
    } else if (isAndroid()) {
      document.documentElement.classList.add("pwa-android");
    }

    // 监听屏幕方向变化
    window.addEventListener("orientationchange", () => {
      setTimeout(() => {
        // 延迟执行以确保视口尺寸已更新
        applyPWAStyles();
      }, 500);
    });
  }
}

/**
 * 监听PWA安装事件
 */
export function setupPWAEventListeners(): void {
  // 监听beforeinstallprompt事件
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    // PWA installation available
  });

  // 监听appinstalled事件
  window.addEventListener("appinstalled", () => {
    // PWA already installed
    applyPWAStyles();
  });
}
