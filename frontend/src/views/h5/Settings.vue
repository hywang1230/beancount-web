<template>
  <div class="settings-page">
    <van-cell-group inset>
      <van-cell
        title="周期记账"
        icon="replay"
        is-link
        @click="navigateTo('/h5/recurring')"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">管理周期性收支记录</span>
        </template>
      </van-cell>

      <van-cell
        title="账户管理"
        icon="manager-o"
        is-link
        @click="navigateTo('/h5/accounts')"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">管理收支账户信息</span>
        </template>
      </van-cell>

      <van-cell
        title="文件管理"
        icon="balance-list-o"
        is-link
        @click="navigateTo('/h5/files')"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">查看和验证账本文件</span>
        </template>
      </van-cell>

      <van-cell
        title="数据同步"
        icon="exchange"
        is-link
        @click="navigateTo('/h5/sync')"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">同步账本到GitHub仓库</span>
        </template>
      </van-cell>
    </van-cell-group>

    <van-cell-group inset title="AI设置">
      <van-cell
        title="AI助手配置"
        icon="chat-o"
        is-link
        @click="showAIConfig = true"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">配置AI模型和参数</span>
        </template>
      </van-cell>

      <van-cell
        title="上下文管理"
        icon="cluster-o"
        is-link
        @click="navigateTo('/h5/ai-context')"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">管理AI对话记忆和上下文</span>
        </template>
      </van-cell>
    </van-cell-group>

    <van-cell-group inset title="外观设置">
      <van-cell title="主题模式" icon="diamond-o" :border="false">
        <template #label>
          <van-radio-group
            v-model="themeSetting"
            @change="handleThemeChange"
            direction="horizontal"
            class="theme-radio-group"
          >
            <van-radio name="light">亮色</van-radio>
            <van-radio name="dark">暗色</van-radio>
            <van-radio name="system">跟随系统</van-radio>
          </van-radio-group>
        </template>
      </van-cell>
    </van-cell-group>

    <van-cell-group inset title="账户管理">
      <van-cell
        title="登出"
        icon="sign-out"
        is-link
        :border="false"
        @click="handleLogout"
        class="logout-cell"
      />
    </van-cell-group>

    <van-cell-group inset title="应用信息">
      <van-cell title="版本信息" icon="info-o" value="1.1.0" :border="false" />

      <van-cell
        title="关于我们"
        icon="question-o"
        is-link
        :border="false"
        @click="showAbout = true"
      />
    </van-cell-group>

    <!-- AI配置对话框 -->
    <van-dialog
      v-model:show="showAIConfig"
      title="AI助手配置"
      :show-cancel-button="true"
      cancel-button-text="取消"
      confirm-button-text="保存"
      @confirm="saveAIConfig"
      @cancel="showAIConfig = false"
      class="ai-config-dialog"
    >
      <div class="ai-config-content">
        <van-form @submit="saveAIConfig">
          <van-field
            v-model="aiConfigForm.llm_model"
            name="llm_model"
            label="模型"
            placeholder="请输入模型名称"
            required
          />
          <van-field
            v-model="aiConfigForm.llm_api_key"
            name="llm_api_key"
            label="API密钥"
            placeholder="请输入API密钥"
            type="password"
            required
          />
          <van-field
            v-model="aiConfigForm.llm_provider_url"
            name="llm_provider_url"
            label="服务地址"
            placeholder="请输入服务地址"
          />
          <van-field
            v-model="aiConfigForm.temperature"
            name="temperature"
            label="创造性"
            placeholder="0-2之间的数值"
            type="number"
          />
          <van-field
            v-model="aiConfigForm.max_tokens"
            name="max_tokens"
            label="最大词数"
            placeholder="请输入最大词数"
            type="number"
          />
          
          <!-- LangSmith配置分组 -->
          <van-divider>LangSmith 监控配置</van-divider>
          
          <van-field name="langsmith_tracing" label="启用追踪">
            <template #input>
              <van-switch 
                v-model="langsmithTracingEnabled" 
                @change="handleLangsmithTracingChange"
              />
            </template>
          </van-field>
          
          <van-field
            v-model="aiConfigForm.langsmith_api_key"
            name="langsmith_api_key"
            label="LangSmith API密钥"
            placeholder="请输入LangSmith API密钥"
            type="password"
            :disabled="!langsmithTracingEnabled"
          />
          
          <van-field
            v-model="aiConfigForm.langsmith_project"
            name="langsmith_project"
            label="项目名称"
            placeholder="请输入项目名称"
            :disabled="!langsmithTracingEnabled"
          />

        </van-form>
      </div>
    </van-dialog>

    <!-- 关于弹窗 -->
    <van-dialog
      v-model:show="showAbout"
      title="关于 Beancount Web"
      message="Beancount Web 是一个基于 Beancount 的记账应用，支持复式记账，帮助您更好地管理个人财务。"
      :show-cancel-button="false"
      confirm-button-text="确定"
    />
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useThemeStore, type ThemeSetting } from "@/stores/theme";
import { showConfirmDialog, showToast } from "vant";
import { computed, ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { aiConfigApi } from "@/api/ai";

const router = useRouter();
const themeStore = useThemeStore();
const authStore = useAuthStore();
const showAbout = ref(false);

// AI配置相关状态
const showAIConfig = ref(false);
const aiConfigLoading = ref(false);
const aiConfigForm = reactive({
  llm_model: 'gpt-3.5-turbo',
  llm_api_key: '',
  llm_provider_url: 'https://api.openai.com/v1',
  temperature: '0.7',
  max_tokens: '2000',
  langsmith_api_key: '',
  langsmith_project: 'beancount-web-ai',
  langsmith_tracing: 'false'
});

// LangSmith追踪开关
const langsmithTracingEnabled = computed({
  get: () => aiConfigForm.langsmith_tracing === 'true',
  set: (value: boolean) => {
    aiConfigForm.langsmith_tracing = value ? 'true' : 'false'
  }
});

// 主题设置
const themeSetting = computed({
  get: () => themeStore.themeSetting,
  set: (value: ThemeSetting) => {
    themeStore.setThemeSetting(value);
  },
});

const navigateTo = (path: string) => {
  router.push(path);
};

// 处理LangSmith追踪开关变化
const handleLangsmithTracingChange = (value: boolean) => {
  if (!value) {
    // 禁用追踪时清空相关字段
    aiConfigForm.langsmith_api_key = '';
  }
};

// AI配置相关函数
const loadAIConfig = async () => {
  try {
    const configs = await aiConfigApi.getConfigsDict();
    
    // 更新配置表单
    Object.keys(aiConfigForm).forEach(key => {
      if (configs.configs[key]) {
        (aiConfigForm as any)[key] = configs.configs[key];
      }
    });
  } catch (error: any) {
    console.error('加载AI配置失败:', error);
  }
};

const saveAIConfig = async () => {
  aiConfigLoading.value = true;
  
  try {
    // 逐个更新配置项
    for (const [key, value] of Object.entries(aiConfigForm)) {
      await aiConfigApi.updateConfig(key, { value: value.toString() });
    }
    
    showToast('AI配置保存成功');
    showAIConfig.value = false;
  } catch (error: any) {
    console.error('保存AI配置失败:', error);
    showToast('保存AI配置失败');
  } finally {
    aiConfigLoading.value = false;
  }
};





// 组件挂载时加载AI配置
onMounted(() => {
  loadAIConfig();
});

const handleThemeChange = (value: ThemeSetting) => {
  const themeNames = {
    light: "亮色模式",
    dark: "暗黑模式",
    system: "跟随系统",
  };
  showToast({
    message: `已切换到${themeNames[value]}`,
    duration: 1500,
  });
};

const handleLogout = async () => {
  try {
    await showConfirmDialog({
      title: "确认登出",
      message: "确定要登出吗？",
      confirmButtonText: "确定",
      cancelButtonText: "取消",
    });

    await authStore.logout();
    showToast("登出成功");
    router.push("/login");
  } catch (error: any) {
    if (error !== "cancel") {
      // console.error("登出失败:", error);
      showToast("登出失败");
    }
  }
};
</script>

<style scoped>
.settings-page {
  padding: 16px;
  background-color: var(--van-background);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

.cell-desc {
  color: var(--van-text-color-3);
  font-size: 12px;
  margin-top: 4px;
}

.theme-radio-group {
  margin-top: 8px;
  gap: 16px;
}

:deep(.van-cell-group__title) {
  padding: 16px 16px 8px;
  color: var(--van-text-color-2);
  font-size: 14px;
  font-weight: normal;
}

:deep(.van-cell) {
  background-color: var(--van-background-2);
  padding: 16px;
}

:deep(.van-cell:last-child::after) {
  display: none;
}

:deep(.van-cell-group--inset) {
  margin: 16px 0;
  border-radius: 8px;
  overflow: hidden;
}

.logout-cell {
  color: var(--van-danger-color);
}

/* AI配置对话框样式 */
.ai-config-dialog :deep(.van-dialog) {
  width: 90%;
  max-width: 400px;
}

.ai-config-content {
  padding: 16px 0;
}


</style>
