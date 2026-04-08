<template>
  <aside class="status-panel flex min-h-0 flex-col px-5 py-5 sm:px-6">
    <div
      class="space-y-5"
      :class="activeRecommendation ? '' : '-mt-2'"
    >
      <div
        v-if="activeRecommendation"
        class="highlight-panel rounded-[28px] p-5 shadow-[0_24px_54px_rgba(134,153,176,0.14)]"
      >
        <p class="text-[11px] uppercase tracking-[0.3em] text-emerald-800/64">
          当前推荐
        </p>
        <h3 class="mt-3 text-2xl font-semibold text-slate-700">
          {{ activeRecommendation.name }}
        </h3>
        <p class="mt-2 text-sm text-slate-600">
          {{ activeRecommendation.category }} · {{ activeRecommendation.budget_tier }}
        </p>
        <p class="mt-3 text-sm font-normal leading-7 text-slate-700">
          {{ activeRecommendation.consultant_summary }}
        </p>
      </div>

      <div class="summary-panel rounded-[28px] p-5">
        <div
          v-if="profileSummary.length"
          class="-mt-1 flex flex-wrap justify-start gap-2"
        >
          <span
            v-for="item in profileSummary"
            :key="item"
            class="summary-chip rounded-full px-3 py-1 text-[15px] font-normal leading-7 text-slate-700"
          >
            {{ item }}
          </span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { ProductRecommendation } from '~/types/chat'

defineProps<{
  activeRecommendation: ProductRecommendation | null
  profileSummary: string[]
}>()
</script>

<style scoped>
.status-panel {
  background:
    linear-gradient(180deg, rgba(244, 250, 248, 0.8), rgba(242, 247, 251, 0.42)),
    radial-gradient(circle at top right, rgba(210, 235, 246, 0.22), transparent 24%);
}

.highlight-panel {
  border: 1px solid rgba(233, 243, 239, 0.95);
  background:
    linear-gradient(180deg, rgba(252, 255, 253, 0.96), rgba(236, 247, 242, 0.8));
}

.summary-panel {
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.52), rgba(240, 247, 250, 0.28));
}

.summary-chip {
  border: 1px solid rgba(255, 255, 255, 0.7);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(244, 248, 250, 0.84));
  box-shadow: 0 10px 24px rgba(148, 163, 184, 0.09);
}
</style>
