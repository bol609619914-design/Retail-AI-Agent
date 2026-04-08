<template>
  <div ref="viewport" class="message-viewport h-full min-h-0 overflow-y-auto border-b border-white/30 px-4 py-5 sm:px-6 lg:border-b-0 lg:border-r">
    <TransitionGroup name="message" tag="div" class="space-y-4">
      <div
        v-for="message in messages"
        :key="message.id"
        class="flex items-start gap-3"
        :class="message.role === 'user' ? 'flex-row-reverse' : ''"
      >
        <div
          class="mt-1 flex h-10 w-10 shrink-0 items-center justify-center"
          :class="message.role === 'assistant' ? 'ai-avatar' : 'user-avatar'"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            :class="message.role === 'assistant' ? 'avatar-icon avatar-icon-ai' : 'avatar-icon avatar-icon-user'"
            aria-hidden="true"
          >
            <circle cx="12" cy="8" r="3.2" />
            <path d="M6.8 18.2C7.5 15.8 9.5 14.4 12 14.4C14.5 14.4 16.5 15.8 17.2 18.2" />
          </svg>
          <span class="sr-only">
            {{ message.role === 'assistant' ? '顾问头像' : '用户头像' }}
          </span>
        </div>

        <div class="max-w-[84%] space-y-3">
          <div
            class="rounded-[24px] px-4 py-3 text-[15px] font-normal leading-7 shadow-[0_12px_30px_rgba(148,163,184,0.10)]"
            :class="message.role === 'assistant'
              ? 'bg-white/82 text-slate-700'
              : 'bg-emerald-50/90 text-slate-800'"
          >
            <template v-if="message.content">
              <div class="whitespace-pre-line">
                {{ message.content }}
              </div>
            </template>
            <template v-else-if="message.isStreaming">
              <span class="streaming-dots" aria-label="顾问正在回复">
                <span />
                <span />
                <span />
              </span>
            </template>
          </div>

          <ChatRecommendationCard
            v-if="message.recommendation"
            :recommendation="message.recommendation"
          />
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import type { ChatMessage } from '~/types/chat'

const props = defineProps<{
  messages: ChatMessage[]
}>()

const viewport = ref<HTMLDivElement | null>(null)

function scrollToBottom() {
  const element = viewport.value
  if (!element) {
    return
  }

  element.scrollTo({
    top: element.scrollHeight,
    behavior: 'smooth'
  })
}

watch(
  () => props.messages.map(message => `${message.id}:${message.content}:${message.isStreaming ? '1' : '0'}:${message.recommendation?.name ?? ''}`).join('|'),
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

onMounted(scrollToBottom)
</script>

<style scoped>
.ai-avatar {
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 8px 24px rgba(148, 163, 184, 0.14);
}

.user-avatar {
  border: 1px solid rgba(255, 255, 255, 0.66);
  border-radius: 9999px;
  background: linear-gradient(135deg, rgba(236, 253, 245, 1), rgba(220, 252, 231, 0.9));
  box-shadow: 0 8px 24px rgba(148, 163, 184, 0.1);
}

.avatar-icon {
  width: 18px;
  height: 18px;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.avatar-icon-ai {
  stroke: rgba(5, 150, 105, 0.9);
}

.avatar-icon-user {
  stroke: rgba(71, 85, 105, 0.9);
}

.streaming-dots {
  display: inline-flex;
  gap: 0.3rem;
  align-items: center;
  min-height: 1.5rem;
}

.streaming-dots span {
  width: 0.42rem;
  height: 0.42rem;
  border-radius: 9999px;
  background: rgba(15, 23, 42, 0.45);
  animation: pulse 1s ease-in-out infinite;
}

.streaming-dots span:nth-child(2) {
  animation-delay: 0.14s;
}

.streaming-dots span:nth-child(3) {
  animation-delay: 0.28s;
}

.message-enter-active {
  transition: opacity 0.32s ease, transform 0.32s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.message-enter-to {
  opacity: 1;
  transform: translateY(0);
}

.message-viewport {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.55) transparent;
  scrollbar-gutter: stable;
}

.message-viewport::-webkit-scrollbar {
  width: 6px;
}

.message-viewport::-webkit-scrollbar-track {
  background: transparent;
}

.message-viewport::-webkit-scrollbar-thumb {
  border: 1px solid transparent;
  border-radius: 9999px;
  background-clip: padding-box;
  background-color: rgba(148, 163, 184, 0.42);
}

.message-viewport::-webkit-scrollbar-thumb:hover {
  background-color: rgba(100, 116, 139, 0.56);
}

@keyframes pulse {
  0%,
  80%,
  100% {
    opacity: 0.28;
    transform: translateY(0);
  }

  40% {
    opacity: 1;
    transform: translateY(-2px);
  }
}
</style>
