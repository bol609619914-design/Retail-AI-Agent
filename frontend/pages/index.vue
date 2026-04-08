<template>
  <div class="chat-page flex min-h-screen items-start justify-center px-4 py-6 sm:px-6 lg:py-8">
    <div class="chat-shell mx-auto flex h-[min(88vh,920px)] w-full max-w-6xl flex-col overflow-hidden rounded-[34px] border border-white/60 bg-white/45 shadow-soft backdrop-blur-2xl">
      <header class="flex flex-wrap items-center justify-between gap-4 border-b border-white/40 px-6 py-5 sm:px-8">
        <div>
          <p class="text-[12px] font-semibold uppercase tracking-[0.28em] text-emerald-700/70">
            Retail AI Agent
          </p>
          <h1 class="mt-2 text-2xl font-normal text-slate-900 sm:text-3xl">
            高端零售顾问对话台
          </h1>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <span
            class="rounded-full border px-4 py-2 text-sm font-medium shadow-[0_10px_30px_rgba(148,163,184,0.12)]"
            :class="demoMode
              ? 'border-amber-200 bg-amber-50/80 text-amber-700'
              : 'border-emerald-200 bg-emerald-50/80 text-emerald-700'"
          >
            {{ demoMode ? '本地演示模式' : '模型在线模式' }}
          </span>
        </div>
      </header>

      <div class="grid min-h-0 flex-1 overflow-hidden lg:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
        <ChatMessageList :messages="messages" />
        <ChatStatusPanel
          :active-recommendation="activeRecommendation"
          :demo-mode="demoMode"
          :profile-summary="profileSummary"
          :status-copy="statusCopy"
          :status-title="statusTitle"
        />
      </div>

      <footer class="border-t border-white/40 px-4 py-5 sm:px-6 sm:py-6">
        <div class="mx-auto w-full max-w-4xl">
          <ChatInputBar
            v-model="draft"
            :disabled="isStreaming"
            @submit="sendMessage"
          />
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
const {
  activeRecommendation,
  demoMode,
  draft,
  isStreaming,
  messages,
  profileSummary,
  sendMessage,
  statusCopy,
  statusTitle
} = useChatConsultant()
</script>

<style scoped>
.chat-page {
  background:
    radial-gradient(circle at top left, rgba(167, 243, 208, 0.24), transparent 26%),
    radial-gradient(circle at bottom right, rgba(255, 255, 255, 0.85), transparent 22%);
}

.chat-shell {
  position: relative;
}

.chat-shell::before {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0.12));
  content: '';
  pointer-events: none;
}
</style>
