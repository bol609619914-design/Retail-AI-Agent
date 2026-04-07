<template>
  <div class="chat-page flex min-h-screen items-center justify-center px-4 py-8 sm:px-6">
    <div class="chat-shell flex h-[min(88vh,920px)] w-full max-w-6xl flex-col overflow-hidden rounded-[34px] border border-white/60 bg-white/45 shadow-soft backdrop-blur-2xl">
      <header class="flex flex-wrap items-center justify-between gap-4 border-b border-white/40 px-6 py-5 sm:px-8">
        <div>
          <p class="text-[11px] uppercase tracking-[0.38em] text-emerald-700/60">
            Retail AI Agent
          </p>
          <h1 class="mt-2 text-2xl font-extralight text-slate-900 sm:text-3xl">
            高端零售顾问对话台
          </h1>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <span
            class="rounded-full border px-3 py-1 text-xs font-light"
            :class="demoMode
              ? 'border-amber-200 bg-amber-50/80 text-amber-700'
              : 'border-emerald-200 bg-emerald-50/80 text-emerald-700'"
          >
            {{ demoMode ? '本地演示模式' : '模型在线模式' }}
          </span>
          <span class="rounded-full bg-white/65 px-4 py-2 text-sm font-light text-slate-500 shadow-[0_10px_30px_rgba(148,163,184,0.12)]">
            中文顾问式推荐
          </span>
        </div>
      </header>

      <div class="grid flex-1 overflow-hidden lg:grid-cols-[1.05fr_0.95fr]">
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

              <div class="max-w-[84%] space-y-3">
                <div
                  class="rounded-[24px] px-4 py-3 text-[15px] leading-7 shadow-[0_12px_30px_rgba(148,163,184,0.10)]"
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

                <div
                  v-if="message.recommendation"
                  class="recommend-card overflow-hidden rounded-[30px] border border-white/60 bg-white/90 shadow-[0_24px_50px_rgba(148,163,184,0.16)]"
                >
                  <div class="recommend-cover relative h-44 overflow-hidden">
                    <img
                      :src="message.recommendation.image"
                      :alt="message.recommendation.name"
                      class="h-full w-full object-cover"
                    >
                    <div class="absolute inset-0 bg-gradient-to-t from-slate-950/55 via-slate-900/10 to-transparent" />
                    <div class="absolute left-5 top-5 flex flex-wrap gap-2">
                      <span class="rounded-full bg-white/85 px-3 py-1 text-[11px] font-light text-slate-700">
                        {{ message.recommendation.category }}
                      </span>
                      <span class="rounded-full bg-white/20 px-3 py-1 text-[11px] font-light text-white backdrop-blur">
                        {{ message.recommendation.brand }}
                      </span>
                    </div>
                    <div class="absolute bottom-5 left-5 right-5">
                      <p class="text-[11px] uppercase tracking-[0.26em] text-white/70">
                        顾问推荐
                      </p>
                      <h3 class="mt-2 text-2xl font-extralight text-white">
                        {{ message.recommendation.name }}
                      </h3>
                      <p class="mt-2 text-sm font-light text-white/82">
                        {{ message.recommendation.price_range }}
                      </p>
                    </div>
                  </div>

                  <div class="space-y-5 px-5 py-5 text-sm font-light leading-7 text-slate-600">
                    <div class="rounded-2xl bg-mint-50/80 p-4">
                      <p class="mb-2 text-xs uppercase tracking-[0.24em] text-emerald-700/60">
                        顾问判断摘要
                      </p>
                      <p>{{ message.recommendation.consultant_summary }}</p>
                    </div>

                    <div class="grid gap-4 sm:grid-cols-2">
                      <div>
                        <p class="mb-1 text-xs uppercase tracking-[0.22em] text-slate-400">
                          品牌
                        </p>
                        <p>{{ message.recommendation.brand }}</p>
                      </div>
                      <div>
                        <p class="mb-1 text-xs uppercase tracking-[0.22em] text-slate-400">
                          价格区间
                        </p>
                        <p>{{ message.recommendation.price_range }}</p>
                      </div>
                    </div>

                    <div>
                      <p class="mb-1 text-xs uppercase tracking-[0.22em] text-slate-400">
                        材质 / 工艺
                      </p>
                      <p>{{ message.recommendation.materials }}</p>
                      <p class="mt-2 text-slate-500">
                        {{ message.recommendation.craftsmanship }}
                      </p>
                    </div>

                    <div>
                      <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
                        专业参数
                      </p>
                      <div class="space-y-2">
                        <div
                          v-for="spec in message.recommendation.signature_specs"
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
                          v-for="preference in message.recommendation.matched_preferences"
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
                          v-for="reason in message.recommendation.why_this"
                          :key="reason"
                          class="rounded-2xl bg-white/80 px-3 py-2 shadow-[0_8px_18px_rgba(148,163,184,0.08)]"
                        >
                          {{ reason }}
                        </li>
                      </ul>
                    </div>

                    <div>
                      <p class="mb-1 text-xs uppercase tracking-[0.22em] text-slate-400">
                        为什么暂不推荐别的
                      </p>
                      <p>{{ message.recommendation.why_not_others }}</p>
                    </div>

                    <div>
                      <p class="mb-2 text-xs uppercase tracking-[0.22em] text-slate-400">
                        适用场景
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

        <aside class="flex flex-col justify-between bg-white/22 px-5 py-5 sm:px-6">
          <div class="space-y-5">
            <div class="rounded-[28px] border border-white/50 bg-white/55 p-5">
              <p class="text-[11px] uppercase tracking-[0.3em] text-slate-400">
                当前状态
              </p>
              <h2 class="mt-3 text-xl font-extralight text-slate-900">
                {{ activeRecommendation ? '已形成推荐' : statusTitle }}
              </h2>
              <p class="mt-3 text-sm font-light leading-7 text-slate-600">
                {{ statusCopy }}
              </p>
            </div>

            <div class="rounded-[28px] border border-white/50 bg-white/55 p-5">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-[11px] uppercase tracking-[0.3em] text-slate-400">
                    运行模式
                  </p>
                  <h3 class="mt-2 text-lg font-extralight text-slate-900">
                    {{ demoMode ? '本地演示模式' : '在线模型模式' }}
                  </h3>
                </div>
                <div
                  class="rounded-full px-3 py-1 text-xs font-light"
                  :class="demoMode ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'"
                >
                  {{ demoMode ? 'Mock' : 'OpenAI' }}
                </div>
              </div>
              <p class="mt-3 text-sm font-light leading-7 text-slate-600">
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
              <h3 class="mt-3 text-2xl font-extralight text-slate-900">
                {{ activeRecommendation.name }}
              </h3>
              <p class="mt-3 text-sm font-light leading-7 text-slate-600">
                {{ activeRecommendation.consultant_summary }}
              </p>
            </div>

            <div class="rounded-[28px] border border-white/50 bg-white/55 p-5">
              <p class="text-[11px] uppercase tracking-[0.3em] text-slate-400">
                顾问节奏
              </p>
              <ul class="mt-3 space-y-2 text-sm font-light leading-7 text-slate-600">
                <li>第一轮先确认空间，例如卧室、客厅或书房。</li>
                <li>第二轮继续收拢氛围或功能重点，例如安静、柔和、香氛或照明。</li>
                <li>第三轮再推荐单品，并解释为什么是这款而不是别的。</li>
              </ul>
            </div>
          </div>

          <footer class="mt-5 border-t border-white/40 pt-5">
            <div class="flex items-center gap-3 rounded-full border border-white/55 bg-white/65 px-5 py-3 shadow-[0_10px_30px_rgba(148,163,184,0.10)]">
              <input
                v-model="draft"
                type="text"
                class="flex-1 border-0 bg-transparent text-[15px] font-light text-slate-700 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
                placeholder="比如：我希望卧室更安静柔和，适合睡前放松"
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
  brand: string
  category: string
  price_range: string
  materials: string
  craftsmanship: string
  signature_specs: string[]
  image: string
  feature: string
  benefit: string
  scenarios: string[]
  matched_preferences: string[]
  why_this: string[]
  why_not_others: string
  consultant_summary: string
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
  mode?: string
  stage?: string
}

const config = useRuntimeConfig()
const draft = ref('')
const isStreaming = ref(false)
const nextId = ref(2)
const messageViewport = ref<HTMLDivElement | null>(null)
const activeRecommendation = ref<ProductRecommendation | null>(null)
const demoMode = ref(true)
const conversationStage = ref<'clarify_space' | 'clarify_atmosphere_or_function' | 'final_recommendation'>('clarify_space')
const messages = ref<ChatMessage[]>([
  {
    id: 1,
    role: 'assistant',
    content: '欢迎来到 Retail AI Agent。先从空间开始吧。你希望我围绕卧室、客厅、书房，还是某个更具体的角落来为你判断？',
    recommendation: null
  }
])

const statusTitle = computed(() => {
  if (conversationStage.value === 'clarify_atmosphere_or_function') {
    return '正在收拢氛围与功能'
  }
  if (conversationStage.value === 'final_recommendation') {
    return '进入单品判断'
  }
  return '仍在理解空间'
})

const statusCopy = computed(() => {
  if (activeRecommendation.value) {
    return '顾问已经形成单品判断，并把理由、命中的偏好点与替代选择说明同步展开。'
  }

  if (conversationStage.value === 'clarify_atmosphere_or_function') {
    return '空间方向已经有了，下一步会继续追问你更偏好的氛围感受或功能重点。'
  }

  if (conversationStage.value === 'final_recommendation') {
    return '信息已经接近足够，顾问正在将偏好收敛成一件更合适的单品。'
  }

  return '当前仍处于第一轮理解阶段，你可以先说空间，再慢慢讲气氛与使用习惯。'
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
  } else if (eventName === 'meta') {
    demoMode.value = payload.mode !== 'openai'
    if (payload.stage === 'clarify_space' || payload.stage === 'clarify_atmosphere_or_function' || payload.stage === 'final_recommendation') {
      conversationStage.value = payload.stage
    }
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

.recommend-cover::after {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(15, 23, 42, 0.2));
  content: '';
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
