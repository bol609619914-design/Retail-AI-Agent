export type ConversationStage =
  | 'clarify_space'
  | 'clarify_atmosphere_or_function'
  | 'final_recommendation'

export interface ProductRecommendation {
  name: string
  brand: string
  category: string
  price_range: string
  budget_tier: string
  materials: string
  craftsmanship: string
  signature_specs: string[]
  style_tags: string[]
  room_tags: string[]
  ideal_for: string[]
  avoid_for: string[]
  pairing_note: string
  image: string
  feature: string
  benefit: string
  scenarios: string[]
  matched_preferences: string[]
  why_this: string[]
  why_not_others: string
  consultant_summary: string
}

export interface ChatMessage {
  id: number
  role: 'assistant' | 'user'
  content: string
  isStreaming?: boolean
  recommendation?: ProductRecommendation | null
}

export interface SseEnvelope {
  text?: string
  product?: ProductRecommendation
  source?: string
  message?: string
  mode?: string
  stage?: ConversationStage
  profile_summary?: string[]
}
