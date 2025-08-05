<template>
  <div class="add-recurring">
    <RecurringForm />
  </div>
</template>

<script setup lang="ts">
import RecurringForm from './components/RecurringForm.vue'
</script>

<style scoped>
.add-recurring {
  min-height: 100vh;
  background-color: #f7f8fa;
}
</style>