import { onMounted, onUnmounted, ref } from "vue";

/**
 * 键盘管理工具
 * 用于检测移动端键盘的显示/隐藏状态
 */
export function useKeyboard() {
  const isKeyboardVisible = ref(false);
  const viewportHeight = ref(0);
  const initialViewportHeight = ref(0);

  // 键盘检测阈值（像素）
  const KEYBOARD_THRESHOLD = 150;

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
    const heightDiff = window.screen.height - viewport.height;

    // 考虑浏览器UI的影响，设置更大的阈值
    if (heightDiff > KEYBOARD_THRESHOLD * 2) {
      isKeyboardVisible.value = true;
    } else {
      isKeyboardVisible.value = false;
    }
  };

  // 监听键盘事件
  const setupKeyboardDetection = () => {
    initialViewportHeight.value = window.innerHeight;
    viewportHeight.value = window.innerHeight;

    // 监听窗口大小变化
    window.addEventListener("resize", detectKeyboard);

    // 如果支持 visualViewport，使用更精确的检测
    if (window.visualViewport) {
      window.visualViewport.addEventListener(
        "resize",
        detectKeyboardWithVisualViewport
      );
    }

    // 监听输入框的焦点事件作为补充
    document.addEventListener("focusin", () => {
      // 延迟检测，等待键盘动画完成
      setTimeout(detectKeyboard, 300);
    });

    document.addEventListener("focusout", () => {
      // 延迟检测，等待键盘隐藏动画完成
      setTimeout(detectKeyboard, 300);
    });
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
