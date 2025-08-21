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
            v-if="showCalculation"
            class="key-item key-action key-plus"
            @touchstart="onKeyTouchStart('plus')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('plus')"
          >
            +
          </div>
          <div
            v-else-if="showNegative"
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
            v-if="showCalculation"
            class="key-item key-action key-minus"
            @touchstart="onKeyTouchStart('minus')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('minus')"
          >
            -
          </div>
          <div
            v-else-if="showDecimal"
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
            v-if="showDecimal"
            class="key-item key-action key-decimal"
            :class="{ 'key-disabled': !canAddDecimal }"
            @touchstart="onKeyTouchStart('decimal')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('decimal')"
          >
            .
          </div>
          <div
            v-if="showCalculation"
            class="key-item key-action key-equals"
            @touchstart="onKeyTouchStart('equals')"
            @touchend="onKeyTouchEnd"
            @click="onKeyClick('equals')"
          >
            =
          </div>
          <div
            v-else-if="showHide"
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
  showCalculation?: boolean; // 新增：是否显示计算功能
}

interface Emits {
  (e: "update:modelValue", value: string): void;
  (e: "update:show", value: boolean): void;
  (e: "confirm", value: string): void;
  (e: "cancel"): void;
  (e: "clear"): void;
  (e: "hide"): void;
  (e: "input", value: string): void;
  (e: "calculate", expression: string, result: string): void; // 新增：计算事件
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
  showCalculation: false, // 新增：默认不显示计算功能
});

const emit = defineEmits<Emits>();

// 内部状态
const inputValue = ref("");
const keyPressed = ref("");

// 计算相关状态
const expression = ref(""); // 当前表达式
const currentOperator = ref(""); // 当前操作符
const previousValue = ref(""); // 上一个操作数
const isCalculating = ref(false); // 是否在计算模式

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
  } else if (key === "plus") {
    handleOperator("+");
  } else if (key === "minus") {
    handleOperator("-");
  } else if (key === "equals") {
    handleEquals();
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

// 处理操作符（加减）
const handleOperator = (operator: string) => {
  if (!props.showCalculation) return;

  const currentValue = inputValue.value;
  if (!currentValue) {
    // 如果没有当前值，但有之前的值，允许更换操作符
    if (previousValue.value && currentOperator.value) {
      currentOperator.value = operator;
    }
    return;
  }

  // 如果已有操作符且有前一个值，说明需要进行中间计算
  if (currentOperator.value && previousValue.value) {
    // 进行中间计算
    const prev = parseFloat(previousValue.value);
    const current = parseFloat(inputValue.value);

    if (!isNaN(prev) && !isNaN(current)) {
      let result = 0;
      switch (currentOperator.value) {
        case "+":
          result = prev + current;
          break;
        case "-":
          result = prev - current;
          break;
        default:
          return;
      }

      // 保留指定的小数位数
      const formattedResult = result
        .toFixed(props.decimalLength)
        .replace(/\.?0+$/, "");

      // 使用计算结果作为下一次运算的第一个操作数
      previousValue.value = formattedResult;
      currentOperator.value = operator;
      inputValue.value = "";
      expression.value = ""; // 清空表达式
      isCalculating.value = true;

      // 更新显示值
      updateValue();
    }
    return;
  }

  // 首次输入操作符：设置第一个操作数和操作符
  previousValue.value = inputValue.value;
  currentOperator.value = operator;
  expression.value = ""; // 清空表达式，让显示逻辑处理
  inputValue.value = "";
  isCalculating.value = true;
};

// 处理等号
const handleEquals = () => {
  if (!props.showCalculation || !currentOperator.value || !previousValue.value)
    return;

  const currentValue = inputValue.value;
  if (!currentValue) return;

  calculateResult();
};

// 计算结果
const calculateResult = () => {
  const prev = parseFloat(previousValue.value);
  const current = parseFloat(inputValue.value);

  if (isNaN(prev) || isNaN(current)) return;

  let result = 0;
  const fullExpression = `${previousValue.value} ${currentOperator.value} ${inputValue.value}`;

  switch (currentOperator.value) {
    case "+":
      result = prev + current;
      break;
    case "-":
      result = prev - current;
      break;
    default:
      return;
  }

  // 保留指定的小数位数
  const formattedResult = result
    .toFixed(props.decimalLength)
    .replace(/\.?0+$/, "");

  // 更新状态
  inputValue.value = formattedResult;
  expression.value = `${fullExpression} = ${formattedResult}`;

  // 重置计算状态
  currentOperator.value = "";
  previousValue.value = "";
  isCalculating.value = false;

  // 触发计算事件
  emit("calculate", fullExpression, formattedResult);
  updateValue();
};

// 清空
const onClear = () => {
  inputValue.value = "";
  // 重置计算状态
  expression.value = "";
  currentOperator.value = "";
  previousValue.value = "";
  isCalculating.value = false;
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
  background: var(--van-background-3);
  color: var(--van-text-color-2);
}

.key-backspace:active {
  background: var(--van-active-color);
}

/* 负号键 */
.key-negative {
  background: var(--van-orange-1);
  color: var(--van-orange-6);
  font-size: 14px;
  font-weight: 600;
}

.key-negative:active {
  background: var(--van-orange-2);
}

/* 小数点键 */
.key-decimal {
  background: var(--van-green-1);
  color: var(--van-green-6);
  font-size: 20px;
  font-weight: bold;
}

.key-decimal:active {
  background: var(--van-green-2);
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

/* 加号键 */
.key-plus {
  background: var(--van-blue-1);
  color: var(--van-blue-6);
  font-size: 18px;
  font-weight: bold;
}

.key-plus:active {
  background: var(--van-blue-2);
}

/* 减号键 */
.key-minus {
  background: var(--van-red-1);
  color: var(--van-red-6);
  font-size: 18px;
  font-weight: bold;
}

.key-minus:active {
  background: var(--van-red-2);
}

/* 等号键 */
.key-equals {
  background: var(--van-green-1);
  color: var(--van-green-6);
  font-size: 18px;
  font-weight: bold;
}

.key-equals:active {
  background: var(--van-green-2);
}

/* 隐藏键 */
.key-hide {
  background: var(--van-background-3);
  color: var(--van-text-color-2);
}

.key-hide:active {
  background: var(--van-active-color);
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

/* 深色模式适配 - 现在使用 Vant 主题变量，无需额外覆盖 */
/* Vant 的深色模式变量会自动适配所有按键样式 */

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
