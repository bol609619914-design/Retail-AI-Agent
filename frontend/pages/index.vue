<template>
  <div class="chat-page flex min-h-screen items-start justify-center px-4 py-6 sm:px-6 lg:py-8">
    <div class="chat-shell mx-auto flex h-[min(88vh,920px)] w-full max-w-6xl flex-col overflow-hidden rounded-[36px] border border-white/60 bg-white/40 shadow-[0_40px_100px_rgba(131,152,175,0.22)] backdrop-blur-[28px]">
      <header class="shell-header flex flex-wrap items-center justify-between gap-4 px-6 py-5 sm:px-8">
        <div class="brand-lockup">
          <p class="wordmark" aria-label="Retail AI Agent">
            <span class="wordmark-retail">Retail</span>
            <span class="wordmark-ai">AI</span>
            <span class="wordmark-agent">Agent</span>
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <span
            class="status-pill rounded-full border px-4 py-2 text-sm font-medium"
            :class="demoMode
              ? 'border-amber-200/80 bg-amber-50/80 text-amber-700'
              : 'border-emerald-200/80 bg-emerald-50/76 text-emerald-700'"
          >
            {{ demoMode ? '本地演示模式' : '模型在线模式' }}
          </span>
        </div>
      </header>

      <div class="grid min-h-0 flex-1 overflow-hidden lg:grid-cols-[minmax(0,1.22fr)_minmax(280px,0.78fr)]">
        <ChatMessageList :messages="messages" />
        <ChatStatusPanel
          :active-recommendation="activeRecommendation"
          :profile-summary="profileSummary"
        />
      </div>

      <footer class="shell-footer px-4 py-5 sm:px-6 sm:py-6">
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
  sendMessage
} = useChatConsultant()
</script>

<style scoped>
.chat-page {
  background:
    radial-gradient(circle at 14% 18%, rgba(173, 236, 202, 0.18), transparent 26%),
    radial-gradient(circle at 88% 12%, rgba(247, 222, 196, 0.34), transparent 24%),
    radial-gradient(circle at 76% 80%, rgba(211, 230, 242, 0.28), transparent 22%);
}

.chat-shell {
  position: relative;
}

.chat-shell::before {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.14)),
    linear-gradient(135deg, rgba(236, 248, 241, 0.68), rgba(252, 247, 240, 0.2));
  content: '';
  pointer-events: none;
}

.chat-shell::after {
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  border: 1px solid rgba(255, 255, 255, 0.42);
  content: '';
  pointer-events: none;
}

.shell-header {
  position: relative;
  border-bottom: 1px solid rgba(255, 255, 255, 0.34);
  background: linear-gradient(180deg, rgba(255, 253, 250, 0.42), rgba(255, 255, 255, 0.08));
}

.shell-footer {
  position: relative;
  border-top: 1px solid rgba(255, 255, 255, 0.34);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 251, 247, 0.26));
}

.brand-lockup {
  display: flex;
  align-items: center;
}

.wordmark {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  font-style: italic;
  letter-spacing: 0.12em;
  color: #58a57e;
  text-shadow:
    0 1px 0 rgba(255, 255, 255, 0.78),
    0 8px 24px rgba(124, 176, 145, 0.16);
}

.wordmark-retail,
.wordmark-ai,
.wordmark-agent {
  font-weight: 700;
  font-style: italic;
  letter-spacing: 0.12em;
  color: #58a57e;
}

.status-pill {
  box-shadow: 0 16px 32px rgba(155, 170, 188, 0.12);
}
</style>
