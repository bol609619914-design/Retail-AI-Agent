<template>
  <div class="recommend-card overflow-hidden rounded-[30px] border border-white/60 bg-white/90 shadow-[0_24px_50px_rgba(148,163,184,0.16)]">
    <div class="recommend-cover relative h-44 overflow-hidden">
      <img
        :src="recommendation.image"
        :alt="recommendation.name"
        class="h-full w-full object-cover"
      >
      <div class="absolute inset-0 bg-gradient-to-t from-slate-950/55 via-slate-900/10 to-transparent" />
      <div class="absolute left-5 top-5 flex flex-wrap gap-2">
        <span class="rounded-full bg-white/85 px-3 py-1 text-[11px] font-medium text-slate-700">
          {{ recommendation.category }}
        </span>
        <span class="rounded-full bg-white/20 px-3 py-1 text-[11px] font-medium text-white backdrop-blur">
          {{ recommendation.brand }}
        </span>
      </div>
      <div class="absolute bottom-5 left-5 right-5">
        <p class="text-[11px] uppercase tracking-[0.26em] text-white/70">
          顾问推荐
        </p>
        <h3 class="mt-2 text-2xl font-semibold text-white">
          {{ recommendation.name }}
        </h3>
        <div class="mt-2 flex flex-wrap gap-2 text-sm font-medium text-white/82">
          <span>{{ recommendation.price_range }}</span>
          <span>·</span>
          <span>{{ recommendation.budget_tier }}</span>
        </div>
      </div>
    </div>

    <div class="space-y-5 px-5 py-5 text-sm font-normal leading-7 text-slate-600">
      <div class="rounded-2xl bg-mint-50/80 p-4">
        <p class="mb-2 text-xs uppercase tracking-[0.24em] text-emerald-700/60">
          顾问判断摘要
        </p>
        <p>{{ recommendation.consultant_summary }}</p>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <p class="mb-1 text-xs uppercase tracking-[0.22em] text-slate-400">
            材质 / 工艺
          </p>
          <p>{{ recommendation.materials }}</p>
          <p class="mt-2 text-slate-500">
            {{ recommendation.craftsmanship }}
          </p>
        </div>
        <div>
          <p class="mb-1 text-xs uppercase tracking-[0.22em] text-slate-400">
            搭配建议
          </p>
          <p>{{ recommendation.pairing_note }}</p>
        </div>
      </div>

      <div>
        <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
          风格 / 空间标签
        </p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tag in [...recommendation.style_tags, ...recommendation.room_tags]"
            :key="tag"
            class="rounded-full bg-slate-50 px-3 py-1 text-xs text-slate-600"
          >
            {{ tag }}
          </span>
        </div>
      </div>

      <div>
        <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
          专业参数
        </p>
        <div class="space-y-2">
          <div
            v-for="spec in recommendation.signature_specs"
            :key="spec"
            class="rounded-2xl bg-slate-50/90 px-3 py-2"
          >
            {{ spec }}
          </div>
        </div>
      </div>

      <div>
        <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
          命中的偏好点
        </p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="preference in recommendation.matched_preferences"
            :key="preference"
            class="rounded-full bg-emerald-50 px-3 py-1 text-xs text-emerald-700"
          >
            {{ preference }}
          </span>
        </div>
      </div>

      <div>
        <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
          为什么选这款
        </p>
        <ul class="space-y-2">
          <li
            v-for="reason in recommendation.why_this"
            :key="reason"
            class="rounded-2xl bg-white/80 px-3 py-2 shadow-[0_8px_18px_rgba(148,163,184,0.08)]"
          >
            {{ reason }}
          </li>
        </ul>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
            更适合哪些人
          </p>
          <ul class="space-y-2">
            <li
              v-for="item in recommendation.ideal_for"
              :key="item"
              class="rounded-2xl bg-emerald-50/70 px-3 py-2"
            >
              {{ item }}
            </li>
          </ul>
        </div>
        <div>
          <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
            暂不优先给谁
          </p>
          <ul class="space-y-2">
            <li
              v-for="item in recommendation.avoid_for"
              :key="item"
              class="rounded-2xl bg-rose-50/70 px-3 py-2"
            >
              {{ item }}
            </li>
          </ul>
        </div>
      </div>

      <div>
        <p class="mb-1 text-xs uppercase tracking-[0.22em] text-slate-400">
          为什么暂不推荐别的
        </p>
        <p>{{ recommendation.why_not_others }}</p>
      </div>

      <div>
        <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
          适用场景
        </p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="scenario in recommendation.scenarios"
            :key="scenario"
            class="rounded-full bg-mint-50 px-3 py-1 text-xs text-slate-600"
          >
            {{ scenario }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ProductRecommendation } from '~/types/chat'

defineProps<{
  recommendation: ProductRecommendation
}>()
</script>

<style scoped>
.recommend-card {
  backdrop-filter: blur(18px);
}

.recommend-cover::after {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(15, 23, 42, 0.2));
  content: '';
}
</style>
