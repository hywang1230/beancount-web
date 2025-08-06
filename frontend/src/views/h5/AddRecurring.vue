<template>
  <div class="add-recurring">
    <RecurringForm />
  </div>
</template>

<script setup lang="ts">
import RecurringForm from "./components/RecurringForm.vue";
</script>

<style scoped>
.add-recurring {
  min-height: 100vh;
  background-color: var(--van-background);
  transition: background-color 0.3s ease;
}
</style>
