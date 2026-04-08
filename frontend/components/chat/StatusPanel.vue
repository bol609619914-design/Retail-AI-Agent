<template>
  <aside class="flex min-h-0 flex-col justify-between bg-white/22 px-5 py-5 sm:px-6">
    <div class="space-y-5">
      <div class="rounded-[28px] border border-white/50 bg-white/55 p-5">
        <p class="text-[11px] uppercase tracking-[0.3em] text-slate-400">
          当前状态
        </p>
        <h2 class="mt-3 text-xl font-semibold text-slate-900">
          {{ statusTitle }}
        </h2>
        <p class="mt-3 text-sm font-normal leading-7 text-slate-600">
          {{ statusCopy }}
        </p>
      </div>

      <div class="rounded-[28px] border border-white/50 bg-white/55 p-5">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-[11px] uppercase tracking-[0.3em] text-slate-400">
              运行模式
            </p>
            <h3 class="mt-2 text-xl font-semibold text-slate-900">
              {{ demoMode ? '本地演示模式' : '在线模型模式' }}
            </h3>
          </div>
          <div
            class="rounded-full px-3 py-1 text-xs font-medium"
            :class="demoMode ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'"
          >
            {{ demoMode ? 'Mock' : 'OpenAI' }}
          </div>
        </div>
        <p class="mt-3 text-sm font-normal leading-7 text-slate-600">
          {{ demoMode
            ? '当前为本地演示模式，已启用模拟顾问回复，适合无 Key 演示和作品展示。'
            : '当前已接入在线模型服务，会按照顾问式对话节奏实时生成回复。'
          }}
        </p>
      </div>

      <div
        v-if="activeRecommendation"
        class="rounded-[28px] border border-white/55 bg-gradient-to-br from-white/85 to-emerald-50/70 p-5 shadow-[0_18px_40px_rgba(148,163,184,0.10)]"
      >
        <p class="text-[11px] uppercase tracking-[0.3em] text-emerald-700/60">
          当前推荐
        </p>
        <h3 class="mt-3 text-2xl font-semibold text-slate-900">
          {{ activeRecommendation.name }}
        </h3>
        <p class="mt-2 text-sm text-slate-500">
          {{ activeRecommendation.category }} · {{ activeRecommendation.budget_tier }}
        </p>
        <p class="mt-3 text-sm font-normal leading-7 text-slate-600">
          {{ activeRecommendation.consultant_summary }}
        </p>
      </div>

      <div class="rounded-[28px] border border-white/50 bg-white/55 p-5">
        <p class="text-[11px] uppercase tracking-[0.3em] text-slate-400">
          当前收敛到的信息
        </p>
        <div
          v-if="profileSummary.length"
          class="mt-3 flex flex-wrap gap-2"
        >
          <span
            v-for="item in profileSummary"
            :key="item"
            class="rounded-full bg-white/80 px-3 py-1 text-xs text-slate-600 shadow-[0_8px_18px_rgba(148,163,184,0.08)]"
          >
            {{ item }}
          </span>
        </div>
        <p
          v-else
          class="mt-3 text-sm font-normal leading-7 text-slate-600"
        >
          还在第一轮了解阶段，先说空间，再慢慢补氛围和功能重点就够了。
        </p>
      </div>

      <div class="rounded-[28px] border border-white/50 bg-white/55 p-5">
        <p class="text-[11px] uppercase tracking-[0.3em] text-slate-400">
          顾问节奏
        </p>
        <ul class="mt-3 space-y-2 text-sm font-normal leading-7 text-slate-600">
          <li>第一轮先确认空间，例如卧室、客厅或书房。</li>
          <li>第二轮继续收拢氛围或功能重点，例如安静、柔和、香氛或照明。</li>
          <li>第三轮再推荐单品，并解释为什么是这款而不是别的。</li>
        </ul>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { ProductRecommendation } from '~/types/chat'

defineProps<{
  activeRecommendation: ProductRecommendation | null
  demoMode: boolean
  profileSummary: string[]
  statusCopy: string
  statusTitle: string
}>()
</script>
