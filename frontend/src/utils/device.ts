/**
 * 设备类型检测工具
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
 * 检测是否为桌面设备
 * @returns boolean
 */
export const isDesktop = (): boolean => {
  return !isMobile() && !isTablet();
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
 * 根据设备类型获取默认路由路径
 * @returns string
 */
export const getDefaultRoute = (): string => {
  const deviceType = getDeviceType();

  switch (deviceType) {
    case "mobile":
    case "tablet":
      return "/h5/dashboard";
    case "desktop":
    default:
      return "/dashboard";
  }
};
