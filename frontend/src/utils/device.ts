/**
 * 设备类型检测工具
 * 注意：由于已移除PC端支持，所有设备都使用H5页面
 */

/**
 * 检测是否为移动设备
 * @returns boolean
 */
export const isMobile = (): boolean => {
  // 检测用户代理字符串
  const userAgent = navigator.userAgent.toLowerCase();
  const mobileKeywords = [
    "android",
    "webos",
    "iphone",
    "ipad",
    "ipod",
    "blackberry",
    "iemobile",
    "opera mini",
    "mobile",
  ];

  const isMobileUA = mobileKeywords.some((keyword) =>
    userAgent.includes(keyword)
  );

  // 检测屏幕尺寸
  const isMobileScreen = window.innerWidth <= 768;

  // 检测触摸设备
  const isTouchDevice =
    "ontouchstart" in window || navigator.maxTouchPoints > 0;

  // 综合判断：用户代理包含移动设备标识，或者屏幕宽度小于768px且支持触摸
  return isMobileUA || (isMobileScreen && isTouchDevice);
};

/**
 * 检测是否为平板设备
 * @returns boolean
 */
export const isTablet = (): boolean => {
  const userAgent = navigator.userAgent.toLowerCase();
  const isTabletUA =
    userAgent.includes("ipad") ||
    (userAgent.includes("android") && !userAgent.includes("mobile"));

  const isTabletScreen = window.innerWidth > 768 && window.innerWidth <= 1024;
  const isTouchDevice =
    "ontouchstart" in window || navigator.maxTouchPoints > 0;

  return isTabletUA || (isTabletScreen && isTouchDevice);
};

/**
 * 获取设备类型
 * @returns 'mobile' | 'tablet' | 'desktop'
 */
export const getDeviceType = (): "mobile" | "tablet" | "desktop" => {
  if (isMobile()) return "mobile";
  if (isTablet()) return "tablet";
  return "desktop";
};

/**
 * 获取默认路由路径
 * 注意：由于已移除PC端支持，所有设备都返回H5路由
 * @returns string
 */
export const getDefaultRoute = (): string => {
  return "/h5/dashboard";
};
