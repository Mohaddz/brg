export type Message = { role: string; content: string }
export type Review = {
  turn: number
  review: Record<string, unknown>
  issues: string[]
}
export type RecordData = {
  conversation?: { messages: Message[] }
  messages?: Message[]
  question?: string
  answer?: string
  seed_index?: number
  scenario?: string
  domain?: string
  subject?: string
  profile?: string
  recipe_version?: string
  screening_passed?: boolean
  screening_scope?: string
  selective_review?: {
    acceptable: boolean
    accuracy: number
    usefulness: number
    naturalness: number
    continuity: number
    baseline_comparison: string
    reason: string
    issues: string[]
  } | null
  remaining_issues?: string[]
  repair_count?: number
  agent_review?: { verdict: string; notes: string; human_review?: string }
  qa_repair?: { feedback: string }
  stop_reason?: string
  family_id?: string
  writer_model?: string
  judge_model?: string
  depth?: string
  grounding_mode?: string
  answer_variants?: {
    turn: number
    user: string
    draft: string
    enhanced: string
    selected: string
  }[]
  turn_reviews?: Review[]
}
export type Row = {
  id: number
  request: string
  scenario: string
  domain: string
  profile: string
  passed: boolean | null
  exchanges: number
  words: number
  seed_index?: number
}
export type Batch = {
  screening_scope?: string
  cost?: {
    reported_cost_usd?: string | number
    unresolved_request_count?: number
    unresolved_cost_upper_bound_usd?: string | number
    observed_key_usage_delta_usd?: string | number
    measurement_note?: string
    completed_conversations?: number
  }
  name: string
  count: number
  passed: number
  flagged: number
  assistant_turns: number
  median_words: number
  domains: Record<string, number>
  malformed: number
  filtered: number
  page: number
  page_size: number
  rows: Row[]
}
export function getMessages(record: RecordData): Message[] {
  return (
    record.conversation?.messages ??
    record.messages ?? [
      { role: "user", content: record.question ?? "" },
      { role: "assistant", content: record.answer ?? "" },
    ]
  )
}
export async function api<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal })
  if (!response.ok)
    throw new Error(
      (await response.json().catch(() => null))?.error ??
        "Could not load data. Check the VM connection."
    )
  return response.json()
}
export function wordCount(text: string) {
  return text.trim().split(/\s+/u).filter(Boolean).length
}
export function batchLabel(name: string) {
  return name.replace(/\.jsonl$/, "").replace(/_/g, " ")
}
