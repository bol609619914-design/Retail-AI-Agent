<template>
  <section class="grid flex-1 items-center gap-6 lg:grid-cols-[1.2fr_0.8fr]">
    <div class="space-y-6">
      <p class="text-sm uppercase tracking-[0.4em] text-emerald-700/70">
        Intelligent retail workflow
      </p>

      <div class="space-y-4">
        <h2 class="max-w-3xl text-5xl font-extralight leading-tight text-slate-900">
          Build a calm, modern retail operations dashboard with Nuxt and FastAPI.
        </h2>
        <p class="max-w-2xl text-lg font-light leading-8 text-slate-600">
          This starter includes Tailwind CSS, Naive UI SSR support, and a minimal FastAPI service
          so you can move straight into product logic.
        </p>
      </div>

      <div class="flex flex-wrap gap-3">
        <n-button type="primary" size="large" round>
          Launch Frontend
        </n-button>
        <n-button ghost size="large" round>
          Connect Backend
        </n-button>
      </div>
    </div>

    <n-card :bordered="false" class="rounded-[28px] bg-white/80 shadow-soft backdrop-blur">
      <template #header>
        <span class="text-base font-light text-slate-800">Starter Checklist</span>
      </template>

      <n-space vertical size="large">
        <div v-for="item in items" :key="item.title" class="rounded-2xl bg-mint-50 p-4">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-base font-light text-slate-800">{{ item.title }}</span>
            <n-tag size="small" round :bordered="false">
              Ready
            </n-tag>
          </div>
          <p class="text-sm font-light leading-6 text-slate-600">
            {{ item.description }}
          </p>
        </div>
      </n-space>
    </n-card>
  </section>
</template>

<script setup lang="ts">
const items = [
  {
    title: 'Nuxt 3 App Shell',
    description: 'Global styles, responsive layout, and a mint-to-white visual foundation are configured.'
  },
  {
    title: 'Naive UI SSR',
    description: 'Nuxt config is prepared to render Naive UI correctly during server-side rendering.'
  },
  {
    title: 'FastAPI Service',
    description: 'A minimal API app with health check routing is ready for extension.'
  }
]
</script>
