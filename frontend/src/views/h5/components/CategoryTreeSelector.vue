<template>
  <van-popup
    v-model:show="visible"
    position="right"
    :style="{ width: '100%', height: '100%' }"
    :teleport="'body'"
    :overlay="false"
    class="fullscreen-popup"
  >
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
      :height="400"
      @click-item="onSelectCategory"
    />
  </van-popup>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

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

// 显示选择器
const show = () => {
  visible.value = true;
  selectedCategoryId.value = "";
  activeMainIndex.value = 0;
};

// 关闭选择器
const close = () => {
  visible.value = false;
  emit("close");
};

defineExpose({
  show,
  close,
});
</script>

<style scoped>
.fullscreen-popup {
  z-index: 2000;
}

.search-section {
  padding: 8px 16px;
  background: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
}
</style>
