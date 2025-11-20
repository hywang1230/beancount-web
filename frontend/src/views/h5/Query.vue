<template>
  <div class="h5-query-page">
    <!-- 查询输入区域 -->
    <van-sticky>
      <div class="query-input-section">
        <van-field
          v-model="queryText"
          type="textarea"
          rows="4"
          placeholder="输入 BQL 查询语句&#10;例如: SELECT account, SUM(position) WHERE account ~ 'Expenses' GROUP BY account"
          @blur="onQueryBlur"
        />
        <div class="query-actions">
          <van-button
            size="small"
            type="primary"
            @click="handleExecuteQuery"
            :loading="executing"
          >
            执行查询
          </van-button>
          <van-button
            size="small"
            @click="showExamples = true"
          >
            示例
          </van-button>
          <van-button
            size="small"
            @click="showFunctions = true"
          >
            函数
          </van-button>
          <van-button
            size="small"
            @click="showSaveDialog = true"
            :disabled="!queryText"
          >
            保存
          </van-button>
          <van-button
            size="small"
            @click="showSavedQueries = true"
          >
            我的查询
          </van-button>
        </div>
      </div>
    </van-sticky>

    <!-- 查询结果 -->
    <div v-if="queryResult" class="query-result">
      <!-- 成功结果 -->
      <div v-if="queryResult.success">
        <van-cell-group title="查询结果">
          <van-cell :title="`共 ${queryResult.row_count} 行`" />
        </van-cell-group>

        <!-- 结果表格 -->
        <div class="result-table" v-if="queryResult.rows.length > 0">
          <table>
            <thead>
              <tr>
                <th v-for="(col, index) in queryResult.columns" :key="index">
                  {{ col }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in queryResult.rows" :key="rowIndex">
                <td v-for="(cell, cellIndex) in row" :key="cellIndex">
                  {{ formatCell(cell) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <van-empty v-else description="查询结果为空" />
      </div>

      <!-- 错误信息 -->
      <div v-else>
        <van-cell-group title="查询错误">
          <van-cell>
            <template #title>
              <div class="error-message">
                {{ queryResult.error }}
              </div>
            </template>
          </van-cell>
        </van-cell-group>
      </div>
    </div>

    <!-- 查询示例弹窗 -->
    <van-popup
      v-model:show="showExamples"
      position="bottom"
      :style="{ height: '70%' }"
    >
      <van-nav-bar
        title="查询示例"
        left-text="关闭"
        @click-left="showExamples = false"
      />
      <van-list>
        <van-cell
          v-for="(example, index) in examples"
          :key="index"
          :title="example.name"
          :label="example.description"
          is-link
          @click="useExample(example)"
        />
      </van-list>
    </van-popup>

    <!-- 函数列表弹窗 -->
    <van-popup
      v-model:show="showFunctions"
      position="bottom"
      :style="{ height: '70%' }"
    >
      <van-nav-bar
        title="可用函数"
        left-text="关闭"
        @click-left="showFunctions = false"
      />
      <van-list>
        <van-cell
          v-for="(func, index) in functions"
          :key="index"
          :title="func.name"
        >
          <template #label>
            <div>{{ func.description }}</div>
            <div class="function-example">示例: {{ func.example }}</div>
          </template>
        </van-cell>
      </van-list>
    </van-popup>

    <!-- 保存查询对话框 -->
    <van-dialog
      v-model:show="showSaveDialog"
      title="保存查询"
      show-cancel-button
      @confirm="handleSaveQuery"
    >
      <van-cell-group inset>
        <van-field
          v-model="saveForm.name"
          label="查询名称"
          placeholder="请输入查询名称"
          required
        />
        <van-field
          v-model="saveForm.description"
          label="描述"
          placeholder="请输入描述（可选）"
          type="textarea"
          rows="2"
        />
      </van-cell-group>
    </van-dialog>

    <!-- 我的查询列表 -->
    <van-popup
      v-model:show="showSavedQueries"
      position="bottom"
      :style="{ height: '70%' }"
    >
      <van-nav-bar
        title="我的查询"
        left-text="关闭"
        @click-left="showSavedQueries = false"
      />
      <van-list>
        <van-swipe-cell v-for="query in savedQueries" :key="query.id">
          <van-cell
            :title="query.name"
            :label="query.description"
            is-link
            @click="useSavedQuery(query)"
          />
          <template #right>
            <van-button
              square
              type="danger"
              text="删除"
              @click="handleDeleteQuery(query.id!)"
            />
          </template>
        </van-swipe-cell>
      </van-list>
      <van-empty
        v-if="savedQueries.length === 0"
        description="暂无保存的查询"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { showToast, showConfirmDialog } from "vant";
import {
  executeQuery,
  getQueryExamples,
  getAvailableFunctions,
  getSavedQueries,
  saveQuery,
  deleteSavedQuery,
  type BQLQueryResponse,
  type BQLQueryExample,
  type BQLFunction,
  type SavedQuery,
} from "@/api/query";

const queryText = ref("");
const executing = ref(false);
const queryResult = ref<BQLQueryResponse | null>(null);

const showExamples = ref(false);
const showFunctions = ref(false);
const showSaveDialog = ref(false);
const showSavedQueries = ref(false);

const examples = ref<BQLQueryExample[]>([]);
const functions = ref<BQLFunction[]>([]);
const savedQueries = ref<SavedQuery[]>([]);

const saveForm = ref({
  name: "",
  description: "",
});

// 执行查询
const handleExecuteQuery = async () => {
  if (!queryText.value.trim()) {
    showToast("请输入查询语句");
    return;
  }

  executing.value = true;
  queryResult.value = null;

  try {
    const result = await executeQuery({ query: queryText.value });
    queryResult.value = result;

    if (result.success) {
      showToast(`查询成功，返回 ${result.row_count} 行`);
    } else {
      showToast("查询失败");
    }
  } catch (error) {
    showToast("查询执行失败");
    console.error(error);
  } finally {
    executing.value = false;
  }
};

// 使用示例查询
const useExample = (example: BQLQueryExample) => {
  queryText.value = example.query;
  showExamples.value = false;
  showToast(`已加载示例: ${example.name}`);
};

// 使用保存的查询
const useSavedQuery = (query: SavedQuery) => {
  queryText.value = query.query;
  showSavedQueries.value = false;
  showToast(`已加载查询: ${query.name}`);
};

// 保存查询
const handleSaveQuery = async () => {
  if (!saveForm.value.name.trim()) {
    showToast("请输入查询名称");
    return;
  }

  try {
    await saveQuery({
      name: saveForm.value.name,
      description: saveForm.value.description,
      query: queryText.value,
    });
    showToast("查询已保存");
    saveForm.value = { name: "", description: "" };
    await loadSavedQueries();
  } catch (error) {
    showToast("保存失败");
    console.error(error);
  }
};

// 删除查询
const handleDeleteQuery = async (id: number) => {
  try {
    await showConfirmDialog({
      title: "确认删除",
      message: "确定要删除这个查询吗？",
    });

    await deleteSavedQuery(id);
    showToast("查询已删除");
    await loadSavedQueries();
  } catch (error) {
    if (error !== "cancel") {
      showToast("删除失败");
      console.error(error);
    }
  }
};

// 加载示例
const loadExamples = async () => {
  try {
    examples.value = await getQueryExamples();
  } catch (error) {
    console.error("加载示例失败:", error);
  }
};

// 加载函数列表
const loadFunctions = async () => {
  try {
    functions.value = await getAvailableFunctions();
  } catch (error) {
    console.error("加载函数列表失败:", error);
  }
};

// 加载保存的查询
const loadSavedQueries = async () => {
  try {
    savedQueries.value = await getSavedQueries();
  } catch (error) {
    console.error("加载保存的查询失败:", error);
  }
};

// 格式化单元格内容
const formatCell = (cell: any): string => {
  if (cell === null || cell === undefined) {
    return "";
  }
  if (typeof cell === "number") {
    return cell.toLocaleString();
  }
  return String(cell);
};

const onQueryBlur = () => {
  // 可以在这里添加查询验证
};

onMounted(() => {
  loadExamples();
  loadFunctions();
  loadSavedQueries();
});
</script>

<style scoped>
.h5-query-page {
  padding: 0;
  background-color: var(--van-background);
  min-height: 100vh;
}

.query-input-section {
  background-color: var(--van-background-2);
  padding: 16px;
}

.query-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.query-result {
  padding: 16px;
}

.result-table {
  overflow-x: auto;
  margin-top: 16px;
  background-color: var(--van-background-2);
  border-radius: 8px;
  padding: 12px;
}

.result-table table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
}

.result-table th {
  background-color: var(--van-primary-color);
  color: white;
  padding: 8px;
  text-align: left;
  font-weight: 500;
  white-space: nowrap;
}

.result-table td {
  padding: 8px;
  border-bottom: 1px solid var(--van-border-color);
  white-space: nowrap;
}

.result-table tr:last-child td {
  border-bottom: none;
}

.error-message {
  color: var(--van-danger-color);
  white-space: pre-wrap;
  word-break: break-word;
}

.function-example {
  margin-top: 4px;
  font-family: monospace;
  font-size: 12px;
  color: var(--van-text-color-3);
}

:deep(.van-field__control) {
  font-family: monospace;
  font-size: 13px;
}
</style>

