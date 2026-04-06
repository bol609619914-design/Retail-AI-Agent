<template>
  <div class="chat-page flex min-h-screen items-center justify-center px-4 py-8 sm:px-6">
    <div class="chat-shell flex h-[min(82vh,760px)] w-full max-w-3xl flex-col overflow-hidden rounded-[32px] border border-white/60 bg-white/45 shadow-soft backdrop-blur-2xl">
      <header class="flex items-center justify-between border-b border-white/40 px-6 py-5 sm:px-8">
        <div>
          <p class="text-[11px] uppercase tracking-[0.38em] text-emerald-700/60">
            Retail AI Agent
          </p>
          <h1 class="mt-2 text-2xl font-extralight text-slate-900">
            Minimal Concierge Chat
          </h1>
        </div>
        <div class="hidden rounded-full bg-white/65 px-4 py-2 text-sm font-light text-slate-500 shadow-[0_10px_30px_rgba(148,163,184,0.12)] sm:block">
          Streaming concierge
        </div>
      </header>

      <div ref="messageViewport" class="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
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
              <template v-if="message.role === 'assistant'">
                <span class="ai-avatar-shape" />
              </template>
              <template v-else>
                <span class="sr-only">User avatar</span>
              </template>
            </div>

            <div
              class="max-w-[78%] rounded-[24px] px-4 py-3 text-[15px] leading-7 shadow-[0_12px_30px_rgba(148,163,184,0.10)]"
              :class="message.role === 'assistant'
                ? 'bg-white/78 text-slate-700'
                : 'bg-emerald-50/90 text-slate-800'"
            >
              <template v-if="message.content">
                {{ message.content }}
              </template>
              <template v-else-if="message.isStreaming">
                <span class="streaming-dots" aria-label="AI is replying">
                  <span />
                  <span />
                  <span />
                </span>
              </template>
            </div>
          </div>
        </TransitionGroup>
      </div>

      <footer class="border-t border-white/40 px-4 py-4 sm:px-6 sm:py-5">
        <div class="flex items-center gap-3 rounded-full border border-white/55 bg-white/65 px-5 py-3 shadow-[0_10px_30px_rgba(148,163,184,0.10)]">
          <input
            v-model="draft"
            type="text"
            class="flex-1 border-0 bg-transparent text-[15px] font-light text-slate-700 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
            placeholder="Describe the atmosphere or lifestyle you want..."
            :disabled="isStreaming"
            @keydown.enter="sendMessage"
          >

          <button
            type="button"
            class="send-button flex h-10 w-10 items-center justify-center rounded-full text-slate-600 transition hover:bg-white/80 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="isStreaming"
            @click="sendMessage"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.8"
              class="h-5 w-5"
              aria-hidden="true"
            >
              <path d="M21 3L9 15" />
              <path d="M21 3L14 21L9 15L3 10L21 3Z" />
            </svg>
            <span class="sr-only">发送</span>
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ChatMessage {
  id: number
  role: 'assistant' | 'user'
  content: string
  isStreaming?: boolean
}

const config = useRuntimeConfig()
const draft = ref('')
const isStreaming = ref(false)
const nextId = ref(2)
const messageViewport = ref<HTMLDivElement | null>(null)
const messages = ref<ChatMessage[]>([
  {
    id: 1,
    role: 'assistant',
    content: '欢迎来到 Retail AI Agent。告诉我你理想中的生活氛围、空间或使用习惯，我会为你慢慢收拢到最合适的一件单品。'
  }
])

function scrollToBottom() {
  const viewport = messageViewport.value
  if (!viewport) {
    return
  }

  viewport.scrollTo({
    top: viewport.scrollHeight,
    behavior: 'smooth'
  })
}

async function sendMessage() {
  const value = draft.value.trim()
  if (!value || isStreaming.value) {
    return
  }

  const userMessage: ChatMessage = {
    id: nextId.value++,
    role: 'user',
    content: value
  }

  messages.value.push(userMessage)
  draft.value = ''
  await nextTick()
  scrollToBottom()

  const requestMessages = messages.value.map(({ role, content }) => ({ role, content }))
  const assistantMessage: ChatMessage = {
    id: nextId.value++,
    role: 'assistant',
    content: '',
    isStreaming: true
  }

  messages.value.push(assistantMessage)
  isStreaming.value = true
  await nextTick()
  scrollToBottom()

  try {
    const response = await fetch(`${config.public.apiBase}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ messages: requestMessages })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || 'Unable to reach the chat service.')
    }

    if (!response.body) {
      throw new Error('Streaming is not available in this browser.')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }

      assistantMessage.content += decoder.decode(value, { stream: true })
      messages.value = [...messages.value]
      await nextTick()
      scrollToBottom()
    }

    assistantMessage.content += decoder.decode()

    if (!assistantMessage.content.trim()) {
      assistantMessage.content = '我暂时没有生成到有效回复，请再试一次。'
    }
  } catch (error) {
    assistantMessage.content = error instanceof Error
      ? `连接顾问服务时出现问题：${error.message}`
      : '连接顾问服务时出现未知问题。'
  } finally {
    assistantMessage.isStreaming = false
    isStreaming.value = false
    messages.value = [...messages.value]
    await nextTick()
    scrollToBottom()
  }
}

onMounted(() => {
  scrollToBottom()
})
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

.ai-avatar {
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 8px 24px rgba(148, 163, 184, 0.14);
}

.ai-avatar-shape {
  display: block;
  width: 18px;
  height: 18px;
  border-radius: 5px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.95), rgba(45, 212, 191, 0.65));
  transform: rotate(45deg);
}

.user-avatar {
  border: 1px solid rgba(255, 255, 255, 0.66);
  border-radius: 9999px;
  background: linear-gradient(135deg, rgba(236, 253, 245, 1), rgba(220, 252, 231, 0.9));
  box-shadow: 0 8px 24px rgba(148, 163, 184, 0.1);
}

.send-button {
  border: 0;
  background: transparent;
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
