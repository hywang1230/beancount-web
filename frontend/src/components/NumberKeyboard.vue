<template>
  <van-popup
    v-model:show="visible"
    position="bottom"
    :style="{ height: 'auto' }"
    :close-on-click-overlay="closeOnClickOverlay"
    :teleport="teleport"
    class="number-keyboard-popup"
    @close="onClose"
  >
    <div class="number-keyboard">
      <!-- 键盘标题栏 -->
      <div class="keyboard-header">
        <div class="keyboard-title">{{ title }}</div>
        <div class="keyboard-actions">
          <van-button
            v-if="showClear"
            type="default"
            size="small"
            @click="onClear"
          >
            清空
          </van-button>
          <van-button
            v-if="showConfirm"
            type="primary"
            size="small"
            @click="onConfirm"
          >
            确认
          </van-button>
        </div>
      </div>

      <!-- 输入值显示区域 -->
      <div class="keyboard-display">
        <div class="display-value">{{ displayValue || placeholder }}</div>
      </div>

      <!-- 键盘按键区域 -->
      <div class="keyboard-keys">
        <div class="key-row">
          <div
            v-for="key in ['1', '2', '3']"
            :key="key"
            class="key-item key-number"
            @touchstart="onKeyTouchStart(key)"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick(key)"
          >
            {{ key }}
          </div>
          <div
            class="key-item key-action key-backspace"
            @touchstart="onKeyTouchStart('backspace')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('backspace')"
          >
            <van-icon name="clear" />
          </div>
        </div>

        <div class="key-row">
          <div
            v-for="key in ['4', '5', '6']"
            :key="key"
            class="key-item key-number"
            @touchstart="onKeyTouchStart(key)"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick(key)"
          >
            {{ key }}
          </div>
          <div
            v-if="showNegative"
            class="key-item key-action key-negative"
            :class="{ 'key-disabled': !canAddNegative }"
            @touchstart="onKeyTouchStart('negative')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('negative')"
          >
            +/-
          </div>
          <div v-else class="key-item key-empty" />
        </div>

        <div class="key-row">
          <div
            v-for="key in ['7', '8', '9']"
            :key="key"
            class="key-item key-number"
            @touchstart="onKeyTouchStart(key)"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick(key)"
          >
            {{ key }}
          </div>
          <div
            v-if="showDecimal"
            class="key-item key-action key-decimal"
            :class="{ 'key-disabled': !canAddDecimal }"
            @touchstart="onKeyTouchStart('decimal')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('decimal')"
          >
            .
          </div>
          <div v-else class="key-item key-empty" />
        </div>

        <div class="key-row">
          <div
            class="key-item key-number key-zero"
            @touchstart="onKeyTouchStart('0')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('0')"
          >
            0
          </div>
          <div
            v-if="showHide"
            class="key-item key-action key-hide"
            @touchstart="onKeyTouchStart('hide')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('hide')"
          >
            <van-icon name="arrow-down" />
          </div>
          <div
            v-else-if="showConfirmInKeys"
            class="key-item key-action key-confirm"
            @touchstart="onKeyTouchStart('confirm')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('confirm')"
          >
            确认
          </div>
          <div v-else class="key-item key-empty" />
        </div>
      </div>
    </div>
  </van-popup>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

interface Props {
  modelValue?: string | number;
  show?: boolean;
  title?: string;
  placeholder?: string;
  maxLength?: number;
  decimalLength?: number;
  showDecimal?: boolean;
  showNegative?: boolean;
  showClear?: boolean;
  showConfirm?: boolean;
  showHide?: boolean;
  showConfirmInKeys?: boolean;
  closeOnClickOverlay?: boolean;
  teleport?: string | HTMLElement;
}

interface Emits {
  (e: "update:modelValue", value: string): void;
  (e: "update:show", value: boolean): void;
  (e: "confirm", value: string): void;
  (e: "cancel"): void;
  (e: "clear"): void;
  (e: "hide"): void;
  (e: "input", value: string): void;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: "",
  show: false,
  title: "数字键盘",
  placeholder: "请输入金额",
  maxLength: 10,
  decimalLength: 2,
  showDecimal: true,
  showNegative: true,
  showClear: true,
  showConfirm: true,
  showHide: false,
  showConfirmInKeys: false,
  closeOnClickOverlay: true,
  teleport: "body",
});

const emit = defineEmits<Emits>();

// 内部状态
const inputValue = ref("");
const keyPressed = ref("");

// 同步外部值
watch(
  () => props.modelValue,
  (newValue) => {
    inputValue.value = String(newValue || "");
  },
  { immediate: true }
);

// 显示状态
const visible = computed({
  get: () => props.show,
  set: (value) => emit("update:show", value),
});

// 显示值
const displayValue = computed(() => {
  if (!inputValue.value) return "";

  // 格式化显示值
  const value = inputValue.value;

  // 如果是负数，确保负号在最前面
  const isNegative = value.startsWith("-");
  const cleanValue = isNegative ? value.slice(1) : value;

  // 添加千分位分隔符（可选）
  // const formattedValue = cleanValue.replace(/\B(?=(\d{3})+(?!\d))/g, ',')

  return isNegative ? `-${cleanValue}` : cleanValue;
});

// 检查是否可以添加小数点
const canAddDecimal = computed(() => {
  if (!props.showDecimal) return false;
  return !inputValue.value.includes(".");
});

// 检查是否可以添加负号
const canAddNegative = computed(() => {
  if (!props.showNegative) return false;
  return !inputValue.value.startsWith("-");
});

// 按键点击处理
const onKeyClick = (key: string) => {
  if (key === "backspace") {
    handleBackspace();
  } else if (key === "decimal") {
    handleDecimal();
  } else if (key === "negative") {
    handleNegative();
  } else if (key === "clear") {
    onClear();
  } else if (key === "confirm") {
    onConfirm();
  } else if (key === "hide") {
    onHide();
  } else if (/^\d$/.test(key)) {
    handleNumber(key);
  }
};

// 处理数字输入
const handleNumber = (num: string) => {
  if (inputValue.value.length >= props.maxLength) return;

  // 如果当前值是0，直接替换
  if (inputValue.value === "0") {
    inputValue.value = num;
  } else {
    inputValue.value += num;
  }

  updateValue();
};

// 处理退格
const handleBackspace = () => {
  if (inputValue.value.length > 0) {
    inputValue.value = inputValue.value.slice(0, -1);
    updateValue();
  }
};

// 处理小数点
const handleDecimal = () => {
  if (!canAddDecimal.value) return;

  // 如果是空值或只有负号，先添加0
  if (!inputValue.value || inputValue.value === "-") {
    inputValue.value = (inputValue.value || "") + "0.";
  } else {
    inputValue.value += ".";
  }

  updateValue();
};

// 处理正负号切换
const handleNegative = () => {
  if (!props.showNegative) return;

  if (inputValue.value.startsWith("-")) {
    // 移除负号
    inputValue.value = inputValue.value.slice(1);
  } else {
    // 添加负号
    inputValue.value = "-" + inputValue.value;
  }

  updateValue();
};

// 更新值
const updateValue = () => {
  // 验证小数位数
  if (inputValue.value.includes(".")) {
    const parts = inputValue.value.split(".");
    if (parts[1] && parts[1].length > props.decimalLength) {
      inputValue.value =
        parts[0] + "." + parts[1].slice(0, props.decimalLength);
    }
  }

  emit("update:modelValue", inputValue.value);
  emit("input", inputValue.value);
};

// 清空
const onClear = () => {
  inputValue.value = "";
  updateValue();
  emit("clear");
};

// 确认
const onConfirm = () => {
  emit("confirm", inputValue.value);
  visible.value = false;
};

// 取消/关闭
const onClose = () => {
  emit("cancel");
};

// 隐藏
const onHide = () => {
  visible.value = false;
  emit("hide");
};

// 按键触摸效果
const onKeyTouchStart = (key: string) => {
  keyPressed.value = key;
};

const onKeyTouchEnd = () => {
  keyPressed.value = "";
};
</script>

<style scoped>
.number-keyboard-popup {
  z-index: 3000;
}

.number-keyboard {
  background: var(--van-background-2);
  padding: 0;
  user-select: none;
  -webkit-user-select: none;
}

/* 键盘标题栏 */
.keyboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--van-background);
  border-bottom: 1px solid var(--van-border-color);
}

.keyboard-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--van-text-color);
}

.keyboard-actions {
  display: flex;
  gap: 8px;
}

.keyboard-actions :deep(.van-button--small) {
  height: 32px;
  padding: 0 12px;
  font-size: 14px;
}

/* 显示区域 */
.keyboard-display {
  padding: 16px 20px;
  background: var(--van-background);
  border-bottom: 1px solid var(--van-border-color);
}

.display-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--van-text-color);
  text-align: right;
  min-height: 32px;
  line-height: 32px;
  letter-spacing: 1px;
}

.display-value:empty::before {
  content: attr(data-placeholder);
  color: var(--van-text-color-3);
  font-weight: normal;
}

/* 键盘按键区域 */
.keyboard-keys {
  padding: 8px;
  background: var(--van-background-2);
}

.key-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.key-row:last-child {
  margin-bottom: 0;
}

.key-item {
  flex: 1;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--van-background);
  border-radius: 8px;
  font-size: 18px;
  font-weight: 600;
  color: var(--van-text-color);
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--van-border-color);
  position: relative;
}

.key-item:active {
  transform: scale(0.95);
  background: var(--van-active-color);
}

/* 数字键 */
.key-number {
  background: var(--van-background);
  color: var(--van-text-color);
}

.key-number:hover {
  background: var(--van-background-3);
}

/* 零键加宽 */
.key-zero {
  flex: 2;
  margin-right: 8px;
}

/* 功能键 */
.key-action {
  background: var(--van-background-3);
  color: var(--van-text-color-2);
  font-size: 16px;
}

.key-action:hover {
  background: var(--van-active-color);
}

/* 退格键 */
.key-backspace {
  background: #f7f8fa;
  color: #646566;
}

.key-backspace:active {
  background: #ebedf0;
}

/* 负号键 */
.key-negative {
  background: #fff7e6;
  color: #fa8c16;
  font-size: 14px;
  font-weight: 600;
}

.key-negative:active {
  background: #fff2d9;
}

/* 小数点键 */
.key-decimal {
  background: #f6ffed;
  color: #52c41a;
  font-size: 20px;
  font-weight: bold;
}

.key-decimal:active {
  background: #f0f9e8;
}

/* 确认键 */
.key-confirm {
  background: var(--van-primary-color);
  color: white;
  font-size: 16px;
}

.key-confirm:active {
  background: var(--van-primary-color-dark);
}

/* 隐藏键 */
.key-hide {
  background: #f7f8fa;
  color: #646566;
}

.key-hide:active {
  background: #ebedf0;
}

/* 空白键 */
.key-empty {
  background: transparent;
  box-shadow: none;
  border: none;
  cursor: default;
}

/* 禁用状态 */
.key-disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

/* 按下效果 */
.key-item.key-pressed {
  transform: scale(0.95);
  background: var(--van-active-color);
}

/* 深色模式适配 */
@media (prefers-color-scheme: dark) {
  .key-backspace {
    background: #2c2c2e;
    color: #8e8e93;
  }

  .key-backspace:active {
    background: #3a3a3c;
  }

  .key-negative {
    background: #2c2415;
    color: #fa8c16;
  }

  .key-negative:active {
    background: #3d3018;
  }

  .key-decimal {
    background: #162312;
    color: #52c41a;
  }

  .key-decimal:active {
    background: #1f2e18;
  }

  .key-hide {
    background: #2c2c2e;
    color: #8e8e93;
  }

  .key-hide:active {
    background: #3a3a3c;
  }
}

/* 响应式设计 */
@media (max-width: 375px) {
  .key-item {
    height: 44px;
    font-size: 16px;
  }

  .display-value {
    font-size: 22px;
  }

  .keyboard-header {
    padding: 10px 16px;
  }

  .keyboard-display {
    padding: 14px 20px;
  }
}

@media (max-width: 320px) {
  .key-item {
    height: 40px;
    font-size: 15px;
  }

  .display-value {
    font-size: 20px;
  }

  .keyboard-keys {
    padding: 6px;
  }

  .key-row {
    gap: 6px;
    margin-bottom: 6px;
  }
}
</style>
