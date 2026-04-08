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
  const messages = ref<ChatMessage[]>([
    {
      id: 1,
      role: 'assistant',
      content: INITIAL_MESSAGE,
      recommendation: null
    }
  ])

  const activeRecommendation = computed(() => {
    for (let index = messages.value.length - 1; index >= 0; index -= 1) {
      const recommendation = messages.value[index]?.recommendation
      if (recommendation) {
        return recommendation
      }
    }
    return null
  })

  const statusTitle = computed(() => {
    if (activeRecommendation.value) {
      return '已形成推荐'
    }
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
      return
    }

    if (eventName === 'meta') {
      demoMode.value = payload.mode !== 'openai'
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
    sendMessage,
    statusCopy,
    statusTitle
  }
}
