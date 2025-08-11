<template>
  <van-popup
    v-model:show="visible"
    position="right"
    :style="{ width: '100%', height: '100%' }"
    :teleport="'body'"
    :overlay="false"
    class="fullscreen-popup"
  >
    <div class="category-selector-container">
      <van-nav-bar
        :title="title"
        left-text="取消"
        left-arrow
        @click-left="close"
      />

      <!-- 搜索框 -->
      <div class="search-section">
        <van-search
          v-model="searchKeyword"
          placeholder="搜索分类..."
          @search="onSearch"
          @input="onSearchInput"
        />
      </div>

      <!-- TreeSelect 组件 -->
      <van-tree-select
        v-model:active-id="selectedCategoryId"
        v-model:main-active-index="activeMainIndex"
        :items="treeSelectItems"
        :height="treeSelectHeight"
        @click-item="onSelectCategory"
        class="tree-select-content"
      />
    </div>
  </van-popup>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";

interface Category {
  name: string;
  displayName?: string;
  hasChildren?: boolean;
  children?: Category[];
}

interface TreeSelectItem {
  text: string;
  children?: TreeSelectChild[];
  disabled?: boolean;
}

interface TreeSelectChild {
  text: string;
  id: string;
  disabled?: boolean;
}

interface Props {
  title?: string;
  categories?: Category[];
}

interface Emits {
  (e: "confirm", value: string): void;
  (e: "close"): void;
}

const props = withDefaults(defineProps<Props>(), {
  title: "选择分类",
  categories: () => [],
});

const emit = defineEmits<Emits>();

// 状态
const visible = ref(false);
const selectedCategoryId = ref("");
const activeMainIndex = ref(0);
const searchKeyword = ref("");
const treeSelectHeight = ref(400);

// 格式化分类名称
const formatCategoryName = (name: string) => {
  // 移除前缀字母和连字符，如 "A-餐饮" -> "餐饮"
  const match = name.match(/^[A-Z]+-(.+)$/);
  if (match) {
    return match[1];
  }
  return name;
};

// 构建TreeSelect数据结构
const treeSelectItems = computed(() => {
  if (!props.categories || props.categories.length === 0) {
    return [];
  }

  // 应用搜索过滤
  let filteredCategories = props.categories;
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase();
    filteredCategories = props.categories.filter(
      (category) =>
        category.name.toLowerCase().includes(keyword) ||
        formatCategoryName(category.name).toLowerCase().includes(keyword)
    );
  }

  // 将扁平的分类数据转换为树形结构
  const rootCategories = new Map<string, TreeSelectItem>();

  filteredCategories.forEach((category) => {
    const parts = category.name.split(":");

    // 跳过顶级分类（Expenses、Income等），从第二级开始
    if (parts.length < 2) return;

    const rootName = formatCategoryName(parts[1]);
    const rootPath = parts.slice(0, 2).join(":");

    if (!rootCategories.has(rootPath)) {
      rootCategories.set(rootPath, {
        text: rootName,
        children: [],
        disabled: false,
      });
    }
  });

  // 为每个根分类收集子项目
  filteredCategories.forEach((category) => {
    const parts = category.name.split(":");
    if (parts.length >= 2) {
      const rootPath = parts.slice(0, 2).join(":");
      const rootCategory = rootCategories.get(rootPath);

      if (rootCategory) {
        // 构建显示名称
        let displayName: string;
        if (parts.length === 2) {
          // 二级分类，直接使用分类名
          displayName = formatCategoryName(parts[1]);
        } else {
          // 三级及以上分类，显示完整路径（去掉前缀）
          displayName = parts
            .slice(2)
            .map((part) => formatCategoryName(part))
            .join(" - ");
        }

        // 检查是否已存在相同的id
        const existingChild = rootCategory.children?.find(
          (child) => child.id === category.name
        );
        if (!existingChild) {
          rootCategory.children?.push({
            text: displayName,
            id: category.name,
            disabled: false,
          });
        }
      }
    }
  });

  return Array.from(rootCategories.values());
});

// 搜索相关方法
const onSearch = () => {
  // 搜索在computed中自动处理
};

const onSearchInput = () => {
  // 输入时自动过滤
};

// 选择分类
const onSelectCategory = (item: TreeSelectChild) => {
  emit("confirm", item.id);
  close();
};

// 计算TreeSelect的高度
const calculateTreeSelectHeight = () => {
  const viewportHeight = window.innerHeight;

  // 动态获取实际元素高度，而不是使用固定值
  const container = document.querySelector(
    ".category-selector-container"
  ) as HTMLElement;
  const navbar = container?.querySelector(".van-nav-bar") as HTMLElement;
  const searchSection = container?.querySelector(
    ".search-section"
  ) as HTMLElement;
  const treeSelect = container?.querySelector(
    ".van-tree-select"
  ) as HTMLElement;

  const actualNavBarHeight = navbar?.offsetHeight || 46;
  const actualSearchSectionHeight = searchSection?.offsetHeight || 64;

  // 在小屏幕下增加更多的安全区域
  let safeAreaBottom = 30; // 增加底部安全区域
  if (viewportHeight < 600) {
    safeAreaBottom = 40; // 小屏幕设备需要更多安全区域
  }
  if (viewportHeight < 500) {
    safeAreaBottom = 50; // 超小屏幕设备需要更多安全区域
  }

  const availableHeight =
    viewportHeight -
    actualNavBarHeight -
    actualSearchSectionHeight -
    safeAreaBottom;

  // 设置最小高度为250px（降低最小高度以适应小屏幕），最大高度为可用高度的90%
  const minHeight = viewportHeight < 600 ? 200 : 250;
  const maxHeightRatio = viewportHeight < 600 ? 0.75 : 0.8;

  const calculatedHeight = Math.max(
    minHeight,
    Math.min(availableHeight, viewportHeight * maxHeightRatio)
  );

  treeSelectHeight.value = calculatedHeight;

  // 直接设置TreeSelect的样式，确保生效
  if (treeSelect) {
    treeSelect.style.setProperty(
      "height",
      calculatedHeight + "px",
      "important"
    );
    treeSelect.style.setProperty(
      "max-height",
      calculatedHeight + "px",
      "important"
    );
    treeSelect.style.setProperty(
      "min-height",
      calculatedHeight + "px",
      "important"
    );

    // 同时设置内部元素的高度
    const nav = treeSelect.querySelector(
      ".van-tree-select__nav"
    ) as HTMLElement;
    const content = treeSelect.querySelector(
      ".van-tree-select__content"
    ) as HTMLElement;

    if (nav) {
      nav.style.setProperty("height", calculatedHeight + "px", "important");
      nav.style.setProperty("max-height", calculatedHeight + "px", "important");
    }

    if (content) {
      content.style.setProperty("height", calculatedHeight + "px", "important");
      content.style.setProperty(
        "max-height",
        calculatedHeight + "px",
        "important"
      );
    }
  }
};

// 显示选择器
const show = () => {
  visible.value = true;
  selectedCategoryId.value = "";
  activeMainIndex.value = 0;

  // 延迟计算高度，确保DOM完全渲染
  nextTick(() => {
    // 再次等待一个微任务，确保所有元素都已经渲染完成
    setTimeout(() => {
      calculateTreeSelectHeight();
    }, 10);
  });
};

// 关闭选择器
const close = () => {
  visible.value = false;
  emit("close");
};

// 窗口尺寸变化时重新计算高度
const handleResize = () => {
  if (visible.value) {
    setTimeout(() => {
      calculateTreeSelectHeight();
    }, 10);
  }
};

// 生命周期钩子
onMounted(() => {
  window.addEventListener("resize", handleResize);
  // 处理设备方向变化
  window.addEventListener("orientationchange", handleResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  window.removeEventListener("orientationchange", handleResize);
});

defineExpose({
  show,
  close,
});
</script>

<style scoped>
.fullscreen-popup {
  z-index: 2000;
}

.category-selector-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--van-background);
}

.search-section {
  flex-shrink: 0;
  padding: 8px 16px;
  background: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
}

.tree-select-content {
  flex: 1;
  overflow: hidden;
}

/* 确保TreeSelect内部滚动正常工作 */
:deep(.van-tree-select) {
  height: v-bind(treeSelectHeight + "px") !important;
  max-height: v-bind(treeSelectHeight + "px") !important;
}

:deep(.van-tree-select__nav),
:deep(.van-tree-select__content) {
  height: 100% !important;
  max-height: 100% !important;
  overflow-y: auto;
}
</style>
