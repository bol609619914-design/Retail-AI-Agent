import type { ChatMessage, ConversationStage, SseEnvelope } from '~/types/chat'

const INITIAL_MESSAGE = '欢迎来到 Retail AI Agent。先从空间开始吧。你希望我围绕卧室、客厅、书房，还是某个更具体的角落来为你判断？'

export function useChatConsultant() {
  const config = useRuntimeConfig()
  const draft = ref('')
  const isStreaming = ref(false)
  const nextId = ref(2)
  const demoMode = ref(true)
  const conversationStage = ref<ConversationStage>('clarify_space')
  const profileSummary = ref<string[]>([])
  const currentRecommendation = ref<ChatMessage['recommendation']>(null)
  const messages = ref<ChatMessage[]>([
    {
      id: 1,
      role: 'assistant',
      content: INITIAL_MESSAGE,
      recommendation: null
    }
  ])

  const activeRecommendation = computed(() => currentRecommendation.value ?? null)

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
      return
    }

    if (eventName === 'product' && payload.product) {
      assistantMessage.recommendation = payload.product
      currentRecommendation.value = payload.product
      return
    }

    if (eventName === 'meta') {
      demoMode.value = payload.mode === 'mock'
      if (payload.stage) {
        conversationStage.value = payload.stage
      }
      profileSummary.value = payload.profile_summary ?? []
      return
    }

    if (eventName === 'error') {
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

    messages.value.push({
      id: nextId.value++,
      role: 'user',
      content: value
    })
    draft.value = ''
    currentRecommendation.value = null

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
        const { done, value: chunk } = await reader.read()
        if (done) {
          break
        }

        buffer += decoder.decode(chunk, { stream: true })
        const { complete, remainder } = extractEvents(buffer)
        buffer = remainder

        for (const rawEvent of complete) {
          applySseEvent(rawEvent, assistantMessage)
        }

        messages.value = [...messages.value]
      }

      buffer += decoder.decode()
      const { complete } = extractEvents(`${buffer}\n\n`)
      for (const rawEvent of complete) {
        applySseEvent(rawEvent, assistantMessage)
      }

      if (!assistantMessage.content.trim()) {
        assistantMessage.content = '我暂时还没有整理出明确判断，你可以再补一句你更想要的氛围或使用方式。'
      }
    } catch (error) {
      assistantMessage.content = error instanceof Error
        ? `连接顾问服务时出现问题：${error.message}`
        : '连接顾问服务时出现了未知问题。'
    } finally {
      assistantMessage.isStreaming = false
      isStreaming.value = false
      messages.value = [...messages.value]
    }
  }

  return {
    activeRecommendation,
    conversationStage,
    demoMode,
    draft,
    isStreaming,
    messages,
    profileSummary,
    sendMessage
  }
}
