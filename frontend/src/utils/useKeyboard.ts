import { onMounted, onUnmounted, ref } from "vue";

/**
 * 键盘管理工具
 * 用于检测移动端键盘的显示/隐藏状态
 */
export function useKeyboard() {
  const isKeyboardVisible = ref(false);
  const viewportHeight = ref(0);
  const initialViewportHeight = ref(0);

  // 检测是否为iOS设备
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);

  // 键盘检测阈值（像素）
  const KEYBOARD_THRESHOLD = isIOS ? 100 : 150;

  const detectKeyboard = () => {
    const currentHeight = window.innerHeight;

    // 如果是第一次初始化，记录初始高度
    if (initialViewportHeight.value === 0) {
      initialViewportHeight.value = currentHeight;
      viewportHeight.value = currentHeight;
      return;
    }

    // 计算高度差
    const heightDiff = initialViewportHeight.value - currentHeight;

    // 根据高度差判断键盘是否显示
    if (heightDiff > KEYBOARD_THRESHOLD) {
      isKeyboardVisible.value = true;
    } else {
      isKeyboardVisible.value = false;
    }

    viewportHeight.value = currentHeight;
  };

  // 使用 visualViewport API 进行更精确的检测
  const detectKeyboardWithVisualViewport = () => {
    if (!window.visualViewport) return;

    const viewport = window.visualViewport;

    if (isIOS) {
      // iOS 特殊处理：使用 visualViewport 的高度变化
      const heightDiff = initialViewportHeight.value - viewport.height;

      console.log("iOS键盘检测:", {
        initialHeight: initialViewportHeight.value,
        currentViewportHeight: viewport.height,
        heightDiff,
        threshold: KEYBOARD_THRESHOLD,
      });

      if (heightDiff > KEYBOARD_THRESHOLD) {
        isKeyboardVisible.value = true;
        console.log("iOS检测到键盘显示");
      } else {
        isKeyboardVisible.value = false;
        console.log("iOS检测到键盘隐藏");
      }
    } else {
      // 其他设备的处理逻辑
      const heightDiff = window.screen.height - viewport.height;

      if (heightDiff > KEYBOARD_THRESHOLD * 2) {
        isKeyboardVisible.value = true;
      } else {
        isKeyboardVisible.value = false;
      }
    }
  };

  // 监听键盘事件
  const setupKeyboardDetection = () => {
    // 初始化高度记录
    if (window.visualViewport) {
      initialViewportHeight.value = window.visualViewport.height;
      viewportHeight.value = window.visualViewport.height;
    } else {
      initialViewportHeight.value = window.innerHeight;
      viewportHeight.value = window.innerHeight;
    }

    console.log("键盘检测初始化:", {
      isIOS,
      initialHeight: initialViewportHeight.value,
      userAgent: navigator.userAgent,
    });

    // 监听窗口大小变化
    window.addEventListener("resize", detectKeyboard);

    // 如果支持 visualViewport，使用更精确的检测
    if (window.visualViewport) {
      window.visualViewport.addEventListener(
        "resize",
        detectKeyboardWithVisualViewport
      );
    }

    // 针对iOS的特殊处理
    if (isIOS) {
      // iOS上，输入框获得焦点时立即检测
      document.addEventListener("focusin", (event) => {
        const target = event.target as HTMLElement;
        if (
          target &&
          (target.tagName === "INPUT" || target.tagName === "TEXTAREA")
        ) {
          console.log("iOS输入框获得焦点:", target);
          // 短延迟等待键盘弹出
          setTimeout(() => {
            if (window.visualViewport) {
              detectKeyboardWithVisualViewport();
            } else {
              detectKeyboard();
            }
          }, 150);
        }
      });

      document.addEventListener("focusout", (event) => {
        const target = event.target as HTMLElement;
        if (
          target &&
          (target.tagName === "INPUT" || target.tagName === "TEXTAREA")
        ) {
          console.log("iOS输入框失去焦点:", target);
          // 短延迟等待键盘隐藏
          setTimeout(() => {
            if (window.visualViewport) {
              detectKeyboardWithVisualViewport();
            } else {
              detectKeyboard();
            }
          }, 150);
        }
      });
    } else {
      // 非iOS设备的焦点事件处理
      document.addEventListener("focusin", () => {
        setTimeout(detectKeyboard, 300);
      });

      document.addEventListener("focusout", () => {
        setTimeout(detectKeyboard, 300);
      });
    }
  };

  const cleanupKeyboardDetection = () => {
    window.removeEventListener("resize", detectKeyboard);

    if (window.visualViewport) {
      window.visualViewport.removeEventListener(
        "resize",
        detectKeyboardWithVisualViewport
      );
    }

    document.removeEventListener("focusin", detectKeyboard);
    document.removeEventListener("focusout", detectKeyboard);
  };

  onMounted(setupKeyboardDetection);
  onUnmounted(cleanupKeyboardDetection);

  return {
    isKeyboardVisible,
    viewportHeight,
    initialViewportHeight,
  };
}
