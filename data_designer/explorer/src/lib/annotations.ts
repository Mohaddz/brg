import type { Message } from "./data"
export const STORAGE_KEY = "saudi-explorer-annotations-v1"
export const verdicts = ["good", "needs_work", "reject", "unrated"] as const
export const issues = [
  "unnatural",
  "repetitive",
  "too_short",
  "too_long",
  "unsupported",
  "constraints",
  "role_confusion",
  "safety",
  "other",
] as const
export type Verdict = (typeof verdicts)[number]
export type Annotation = {
  schema_version: 1
  dataset: string
  record_sha256: string
  target: "conversation" | number
  row: number
  seed_index?: number
  topic?: string
  recipe_version?: string
  messages: Message[]
  verdict: Verdict
  issues: string[]
  notes: string
  updated_at: string
}
export function canonical(value: unknown): string {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]"
  if (value && typeof value === "object")
    return (
      "{" +
      Object.keys(value)
        .sort()
        .map(
          (k) =>
            JSON.stringify(k) +
            ":" +
            canonical((value as Record<string, unknown>)[k])
        )
        .join(",") +
      "}"
    )
  return JSON.stringify(value)
}
export async function fingerprint(record: unknown) {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(canonical(record))
  )
  return Array.from(new Uint8Array(digest), (b) =>
    b.toString(16).padStart(2, "0")
  ).join("")
}
export function key(
  entry: Pick<Annotation, "dataset" | "record_sha256" | "target">
) {
  return JSON.stringify([entry.dataset, entry.record_sha256, entry.target])
}
export function validate(entry: Annotation): Annotation {
  if (
    !entry ||
    entry.schema_version !== 1 ||
    typeof entry.dataset !== "string" ||
    !entry.dataset ||
    !/^[a-f0-9]{64}$/.test(entry.record_sha256) ||
    !verdicts.includes(entry.verdict) ||
    !(
      entry.target === "conversation" ||
      (Number.isInteger(entry.target) && entry.target >= 0)
    ) ||
    !Array.isArray(entry.issues) ||
    entry.issues.some((i) => !issues.includes(i as (typeof issues)[number])) ||
    typeof entry.notes !== "string" ||
    !Array.isArray(entry.messages) ||
    entry.messages.some(
      (m) => !m || typeof m.role !== "string" || typeof m.content !== "string"
    ) ||
    (entry.target !== "conversation" &&
      entry.target >= entry.messages.length) ||
    typeof entry.updated_at !== "string" ||
    Number.isNaN(Date.parse(entry.updated_at))
  )
    throw new Error(
      "Invalid annotation. Import an annotation export, not a dataset."
    )
  return entry
}
export function readAnnotations(): { entries: Annotation[]; error: string } {
  try {
    const entries = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]")
    if (!Array.isArray(entries)) throw new Error("Invalid format")
    entries.forEach(validate)
    return { entries, error: "" }
  } catch {
    return {
      entries: [],
      error:
        "Saved annotations could not be read. Import your backup before reviewing.",
    }
  }
}
export function saveAnnotations(entries: Annotation[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries))
}
export function mergeAnnotations(
  previous: Annotation[],
  imported: Annotation[]
) {
  imported.forEach(validate)
  return [
    ...new Map(
      [...previous, ...imported].map((entry) => [key(entry), entry])
    ).values(),
  ]
}
