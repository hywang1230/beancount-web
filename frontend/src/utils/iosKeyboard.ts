/**
 * iOS键盘检测专用工具
 * 针对iOS Safari的特殊键盘行为进行优化
 */

import { ref } from "vue";

// 检测是否为iOS设备
export const isIOSDevice = () => {
  return (
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
  );
};

// iOS键盘管理器
export function useIOSKeyboard() {
  const isKeyboardVisible = ref(false);

  // iOS键盘检测函数
  const detectIOSKeyboard = () => {
    if (!isIOSDevice()) return false;

    // 方法1：使用visualViewport（推荐）
    if (window.visualViewport) {
      const viewport = window.visualViewport;
      const windowHeight = window.outerHeight || window.screen.height;
      const keyboardHeight =
        windowHeight - viewport.height - viewport.offsetTop;

      console.log("iOS键盘检测 - visualViewport:", {
        windowHeight,
        viewportHeight: viewport.height,
        offsetTop: viewport.offsetTop,
        keyboardHeight,
        isVisible: keyboardHeight > 100,
      });

      return keyboardHeight > 100; // 键盘高度超过100px认为是显示状态
    }

    // 方法2：回退到innerHeight检测
    const heightDiff = window.screen.height - window.innerHeight;
    console.log("iOS键盘检测 - innerHeight:", {
      screenHeight: window.screen.height,
      innerHeight: window.innerHeight,
      heightDiff,
      isVisible: heightDiff > 200,
    });

    return heightDiff > 200; // 高度差超过200px认为键盘显示
  };

  // 强制隐藏底部导航栏（CSS方式）
  const forceHideTabbar = () => {
    const tabbar = document.querySelector(".van-tabbar");
    if (tabbar) {
      (tabbar as HTMLElement).style.transform = "translateY(100%)";
      (tabbar as HTMLElement).style.transition = "transform 0.3s ease";
      console.log("强制隐藏iOS底部导航栏");
    }
  };

  // 恢复底部导航栏显示
  const restoreTabbar = () => {
    const tabbar = document.querySelector(".van-tabbar");
    if (tabbar) {
      (tabbar as HTMLElement).style.transform = "translateY(0)";
      console.log("恢复iOS底部导航栏显示");
    }
  };

  // 设置iOS键盘监听
  const setupIOSKeyboardDetection = () => {
    if (!isIOSDevice()) return;

    console.log("设置iOS键盘检测");

    // 监听输入框焦点
    document.addEventListener("focusin", (event) => {
      const target = event.target as HTMLElement;
      if (target && ["INPUT", "TEXTAREA"].includes(target.tagName)) {
        console.log("iOS输入框获得焦点，强制隐藏导航栏");
        // 立即隐藏导航栏，不等检测结果
        forceHideTabbar();
        isKeyboardVisible.value = true;

        // 延迟检测确认
        setTimeout(() => {
          const isVisible = detectIOSKeyboard();
          if (!isVisible) {
            console.log("延迟检测发现键盘未显示，恢复导航栏");
            restoreTabbar();
            isKeyboardVisible.value = false;
          }
        }, 300);
      }
    });

    document.addEventListener("focusout", (event) => {
      const target = event.target as HTMLElement;
      if (target && ["INPUT", "TEXTAREA"].includes(target.tagName)) {
        console.log("iOS输入框失去焦点，恢复导航栏");
        // 延迟恢复，确保键盘完全隐藏
        setTimeout(() => {
          restoreTabbar();
          isKeyboardVisible.value = false;
        }, 300);
      }
    });

    // 监听visualViewport变化（如果支持）
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", () => {
        const isVisible = detectIOSKeyboard();
        console.log("iOS visualViewport变化，键盘状态:", isVisible);

        if (isVisible) {
          forceHideTabbar();
          isKeyboardVisible.value = true;
        } else {
          // 检查是否有活跃的输入框
          const activeElement = document.activeElement;
          if (
            !activeElement ||
            !["INPUT", "TEXTAREA"].includes(
              (activeElement as HTMLElement).tagName
            )
          ) {
            restoreTabbar();
            isKeyboardVisible.value = false;
          }
        }
      });
    }
  };

  return {
    isKeyboardVisible,
    setupIOSKeyboardDetection,
    forceHideTabbar,
    restoreTabbar,
    detectIOSKeyboard,
  };
}

// 全局iOS键盘管理器实例
let globalIOSKeyboard: ReturnType<typeof useIOSKeyboard> | null = null;

export const getGlobalIOSKeyboard = () => {
  if (!globalIOSKeyboard) {
    globalIOSKeyboard = useIOSKeyboard();
  }
  return globalIOSKeyboard;
};
