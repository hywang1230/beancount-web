<template>
  <div class="edit-recurring">
    <RecurringForm 
      :is-edit="true" 
      :edit-id="editId" 
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import RecurringForm from './components/RecurringForm.vue'

const route = useRoute()

const editId = computed(() => route.params.id as string)
</script>

<style scoped>
.edit-recurring {
  min-height: 100vh;
  background-color: #f7f8fa;
}
</style>