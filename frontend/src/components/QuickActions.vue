<template>
  <van-action-sheet
    v-model:show="show"
    :actions="actions"
    cancel-text="取消"
    close-on-click-action
    @select="onSelect"
  />
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const show = ref(false);

const actions = [
  { name: "快速支出", icon: "minus", color: "#ee0a24", action: "expense" },
  { name: "快速收入", icon: "plus", color: "#07c160", action: "income" },
  { name: "转账", icon: "exchange", color: "#1989fa", action: "transfer" },
  { name: "查看预算", icon: "bar-chart-o", color: "#ff976a", action: "budget" },
];

const onSelect = (item: any) => {
  switch (item.action) {
    case "expense":
      router.push("/h5/add-transaction?type=expense");
      break;
    case "income":
      router.push("/h5/add-transaction?type=income");
      break;
    case "transfer":
      router.push("/h5/add-transaction?type=transfer");
      break;
    case "budget":
      router.push("/h5/budgets");
      break;
  }
};

const open = () => {
  show.value = true;
};

defineExpose({
  open,
});
</script>

