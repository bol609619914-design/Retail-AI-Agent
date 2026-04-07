<template>
  <div class="chat-page flex min-h-screen items-center justify-center px-4 py-8 sm:px-6">
    <div class="chat-shell flex h-[min(86vh,860px)] w-full max-w-5xl flex-col overflow-hidden rounded-[32px] border border-white/60 bg-white/45 shadow-soft backdrop-blur-2xl">
      <header class="flex items-center justify-between border-b border-white/40 px-6 py-5 sm:px-8">
        <div>
          <p class="text-[11px] uppercase tracking-[0.38em] text-emerald-700/60">
            Retail AI Agent
          </p>
          <h1 class="mt-2 text-2xl font-extralight text-slate-900">
            高端零售顾问对话台
          </h1>
        </div>
        <div class="hidden rounded-full bg-white/65 px-4 py-2 text-sm font-light text-slate-500 shadow-[0_10px_30px_rgba(148,163,184,0.12)] sm:block">
          中文流式推荐体验
        </div>
      </header>

      <div class="grid flex-1 overflow-hidden lg:grid-cols-[1.1fr_0.9fr]">
        <div ref="messageViewport" class="overflow-y-auto border-b border-white/30 px-4 py-5 sm:px-6 lg:border-b-0 lg:border-r">
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
                  <span class="sr-only">用户头像</span>
                </template>
              </div>

              <div class="max-w-[82%] space-y-3">
                <div
                  class="rounded-[24px] px-4 py-3 text-[15px] leading-7 shadow-[0_12px_30px_rgba(148,163,184,0.10)]"
                  :class="message.role === 'assistant'
                    ? 'bg-white/80 text-slate-700'
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

                <div
                  v-if="message.recommendation"
                  class="recommend-card rounded-[28px] border border-emerald-100/80 bg-white/85 p-5 shadow-[0_18px_40px_rgba(148,163,184,0.10)]"
                >
                  <div class="mb-4 flex items-start justify-between gap-3">
                    <div>
                      <p class="text-[11px] uppercase tracking-[0.28em] text-emerald-700/60">
                        推荐单品
                      </p>
                      <h3 class="mt-2 text-xl font-extralight text-slate-900">
                        {{ message.recommendation.name }}
                      </h3>
                    </div>
                    <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-light text-emerald-700">
                      顾问精选
                    </span>
                  </div>

                  <div class="space-y-4 text-sm font-light leading-7 text-slate-600">
                    <div>
                      <p class="mb-1 text-xs uppercase tracking-[0.22em] text-slate-400">
                        核心功能
                      </p>
                      <p>{{ message.recommendation.feature }}</p>
                    </div>

                    <div>
                      <p class="mb-1 text-xs uppercase tracking-[0.22em] text-slate-400">
                        用户利益
                      </p>
                      <p>{{ message.recommendation.benefit }}</p>
                    </div>

                    <div>
                      <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
                        场景
                      </p>
                      <div class="flex flex-wrap gap-2">
                        <span
                          v-for="scenario in message.recommendation.scenarios"
                          :key="scenario"
                          class="rounded-full bg-mint-50 px-3 py-1 text-xs text-slate-600"
                        >
                          {{ scenario }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TransitionGroup>
        </div>

        <aside class="flex flex-col justify-between bg-white/20 px-5 py-5 sm:px-6">
          <div class="space-y-5">
            <div class="rounded-[28px] border border-white/50 bg-white/55 p-5">
              <p class="text-[11px] uppercase tracking-[0.3em] text-slate-400">
                当前状态
              </p>
              <h2 class="mt-3 text-xl font-extralight text-slate-900">
                {{ activeRecommendation ? '已形成推荐' : '仍在理解偏好' }}
              </h2>
              <p class="mt-3 text-sm font-light leading-7 text-slate-600">
                {{ statusCopy }}
              </p>
            </div>

            <div
              v-if="activeRecommendation"
              class="rounded-[28px] border border-white/55 bg-gradient-to-br from-white/85 to-emerald-50/70 p-5 shadow-[0_18px_40px_rgba(148,163,184,0.10)]"
            >
              <p class="text-[11px] uppercase tracking-[0.3em] text-emerald-700/60">
                当前推荐
              </p>
              <h3 class="mt-3 text-2xl font-extralight text-slate-900">
                {{ activeRecommendation.name }}
              </h3>
              <p class="mt-3 text-sm font-light leading-7 text-slate-600">
                {{ activeRecommendation.benefit }}
              </p>
            </div>

            <div class="rounded-[28px] border border-white/50 bg-white/55 p-5">
              <p class="text-[11px] uppercase tracking-[0.3em] text-slate-400">
                对话提示
              </p>
              <ul class="mt-3 space-y-2 text-sm font-light leading-7 text-slate-600">
                <li>尽量用中文描述你想要的空间氛围。</li>
                <li>可以直接说卧室、书房、客厅或送礼场景。</li>
                <li>越具体，顾问越容易收敛到单一产品。</li>
              </ul>
            </div>
          </div>

          <footer class="mt-5 border-t border-white/40 pt-5">
            <div class="flex items-center gap-3 rounded-full border border-white/55 bg-white/65 px-5 py-3 shadow-[0_10px_30px_rgba(148,163,184,0.10)]">
              <input
                v-model="draft"
                type="text"
                class="flex-1 border-0 bg-transparent text-[15px] font-light text-slate-700 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
                placeholder="比如：我想给卧室增加更柔和安静的夜间氛围"
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
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ProductRecommendation {
  name: string
  feature: string
  benefit: string
  scenarios: string[]
}

interface ChatMessage {
  id: number
  role: 'assistant' | 'user'
  content: string
  isStreaming?: boolean
  recommendation?: ProductRecommendation | null
}

interface SseEnvelope {
  text?: string
  product?: ProductRecommendation
  source?: string
  message?: string
}

const config = useRuntimeConfig()
const draft = ref('')
const isStreaming = ref(false)
const nextId = ref(2)
const messageViewport = ref<HTMLDivElement | null>(null)
const activeRecommendation = ref<ProductRecommendation | null>(null)
const messages = ref<ChatMessage[]>([
  {
    id: 1,
    role: 'assistant',
    content: '欢迎来到 Retail AI Agent。请用中文告诉我，你更在意空间氛围、日常功能，还是某种具体场景，我会尽量为你收敛到最合适的一件单品。',
    recommendation: null
  }
])

const statusCopy = computed(() => {
  if (activeRecommendation.value) {
    return '顾问已经基于你的偏好收敛出一款更合适的产品，并同步展示了结构化推荐卡片。'
  }

  if (isStreaming.value) {
    return '顾问正在实时生成回复，并尝试从产品库中判断是否已经足够形成单品推荐。'
  }

  return '你可以继续补充偏好，例如空间、光线、香氛、安静程度或生活方式关键词。'
})

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

function extractEvents(buffer: string) {
  const parts = buffer.split('\n\n')
  return {
    complete: parts.slice(0, -1),
    remainder: parts.at(-1) ?? ''
  }
}

function applySseEvent(rawEvent: string, assistantMessage: ChatMessage) {
  const lines = rawEvent.split('\n')
  const eventLine = lines.find(line => line.startsWith('event:'))
  const dataLine = lines.find(line => line.startsWith('data:'))
  const eventName = eventLine?.slice(6).trim()
  const payloadText = dataLine?.slice(5).trim()

  if (!eventName || !payloadText) {
    return
  }

  const payload = JSON.parse(payloadText) as SseEnvelope
  if (eventName === 'chunk' && payload.text) {
    assistantMessage.content += payload.text
  } else if (eventName === 'product' && payload.product) {
    assistantMessage.recommendation = payload.product
    activeRecommendation.value = payload.product
  } else if (eventName === 'error') {
    assistantMessage.content = payload.message
      ? `顾问服务暂时有些不稳定：${payload.message}`
      : '顾问服务暂时有些不稳定，请稍后再试。'
  }
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
    isStreaming: true,
    recommendation: null
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
      throw new Error(errorText || '顾问服务暂时不可用。')
    }

    if (!response.body) {
      throw new Error('当前浏览器不支持流式读取。')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const { complete, remainder } = extractEvents(buffer)
      buffer = remainder

      for (const rawEvent of complete) {
        applySseEvent(rawEvent, assistantMessage)
      }

      messages.value = [...messages.value]
      await nextTick()
      scrollToBottom()
    }

    buffer += decoder.decode()
    const { complete } = extractEvents(`${buffer}\n\n`)
    for (const rawEvent of complete) {
      applySseEvent(rawEvent, assistantMessage)
    }

    if (!assistantMessage.content.trim()) {
      assistantMessage.content = '我暂时没有整理出明确回复，你可以再补充一点你想要的空间感受。'
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

.recommend-card {
  backdrop-filter: blur(18px);
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