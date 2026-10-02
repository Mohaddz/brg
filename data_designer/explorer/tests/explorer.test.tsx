import { beforeEach, describe, expect, it, vi } from "vitest"
import { resources } from "../src/lib/resources"

beforeEach(() => resources.clear())
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { createHash } from "node:crypto"
import App from "../src/App"
import { ThemeProvider } from "../src/components/theme-provider"
import {
  canonical,
  fingerprint,
  mergeAnnotations,
  readAnnotations,
  saveAnnotations,
  STORAGE_KEY,
  type Annotation,
} from "../src/lib/annotations"

const record = {
  seed_index: 0,
  domain: "writing",
  scenario: "كتابة رسالة بسيطة",
  screening_passed: true,
  conversation: {
    messages: [
      { role: "user", content: "ابي رسالة بسيطة" },
      {
        role: "assistant",
        content: "هذه رسالة مناسبة.\n\n**تقدر تعدلها** على حسب الموقف.",
      },
    ],
  },
  answer_variants: [
    {
      turn: 1,
      user: "ابي رسالة بسيطة",
      draft: "مسودة أصلية",
      enhanced: "إجابة محسنة أطول",
      selected: "enhanced",
    },
  ],
  turn_reviews: [
    {
      turn: 1,
      review: {
        preferred: "enhanced",
        reason: "أوضح وأنسب",
        draft_completeness: 3,
        enhanced_completeness: 4,
        enhanced_adds_value: true,
      },
      issues: [],
    },
  ],
}
const row = {
  id: 0,
  request: "ابي رسالة بسيطة",
  scenario: "كتابة رسالة بسيطة",
  domain: "writing",
  profile: "practical",
  passed: true,
  exchanges: 1,
  words: 10,
}
const annotation = (): Annotation => ({
  schema_version: 1,
  dataset: "saudi_hybrid_pilot_v1.jsonl",
  record_sha256: "a".repeat(64),
  target: "conversation",
  row: 1,
  messages: record.conversation.messages,
  verdict: "good",
  issues: [],
  notes: "مناسب",
  updated_at: new Date().toISOString(),
})
function mockApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input === "/api/datasets")
        return Response.json([
          { name: "saudi_hybrid_pilot_v1.jsonl", bytes: 500 },
        ])
      if (input.includes("/records/")) return Response.json(record)
      const params = new URL("http://localhost" + input).searchParams
      const rows =
        params.get("status") === "flagged" || params.get("search") === "missing"
          ? []
          : [row]
      return Response.json({
        name: "saudi_hybrid_pilot_v1.jsonl",
        count: 1,
        passed: 1,
        flagged: 0,
        assistant_turns: 1,
        median_words: 10,
        domains: { writing: 1 },
        malformed: 0,
        filtered: rows.length,
        page: 0,
        page_size: 100,
        rows,
      })
    })
  )
}
describe("annotation compatibility", () => {
  it("preserves the original canonical SHA256 including Arabic and nested objects", async () => {
    const expected = createHash("sha256")
      .update(canonical(record), "utf8")
      .digest("hex")
    expect(await fingerprint(record)).toBe(expected)
    expect(canonical({ b: "عربي", a: { z: 2, x: 1 } })).toBe(
      '{"a":{"x":1,"z":2},"b":"عربي"}'
    )
  })
  it("merges reviews by dataset, record and target while preserving message reviews", () => {
    const original = annotation()
    const message = { ...original, target: 1 as const }
    const merged = mergeAnnotations(
      [original, message],
      [{ ...original, notes: "updated" }]
    )
    expect(merged).toHaveLength(2)
    expect(merged[0].notes).toBe("updated")
    saveAnnotations(merged)
    expect(readAnnotations().entries).toEqual(merged)
    expect(() =>
      mergeAnnotations(merged, [{ ...original, target: 99 }])
    ).toThrow()
  })
  it("blocks corrupted storage without overwriting it", () => {
    localStorage.setItem(STORAGE_KEY, "broken")
    expect(readAnnotations().error).toContain("Import your backup")
    expect(localStorage.getItem(STORAGE_KEY)).toBe("broken")
  })
})
describe("review workspace", () => {
  it("requests dataset-wide reply sorting and switches to smallest first", async () => {
    history.replaceState(null, "", "/")
    mockApi()
    const user = userEvent.setup()
    render(
      <ThemeProvider>
        <App />
      </ThemeProvider>
    )
    await screen.findByText("هذه رسالة مناسبة.")
    expect(
      vi
        .mocked(fetch)
        .mock.calls.some(([url]) => String(url).includes("sort=reply_desc"))
    ).toBe(true)
    fireEvent.click(
      screen.getByRole("button", { name: "Library", exact: true })
    )
    await user.click(screen.getByRole("combobox", { name: "Reply size order" }))
    await user.click(
      screen.getByRole("option", { name: "Shortest replies first" })
    )
    await waitFor(() =>
      expect(
        vi.mocked(fetch).mock.calls.some(([url]) => {
          const params = new URL(String(url), "http://localhost").searchParams
          return (
            params.get("sort") === "reply_asc" && params.get("page") === "0"
          )
        })
      ).toBe(true)
    )
  })
  it("switches to a prefetched chat without loading blocks or mismatched content", async () => {
    const second = {
      ...record,
      conversation: {
        messages: [
          { role: "user", content: "Second request" },
          { role: "assistant", content: "**Second response**" },
        ],
      },
    }
    const fetcher = vi.fn(async (input: string) => {
      if (input === "/api/datasets")
        return Response.json([
          { name: "saudi_hybrid_pilot_v1.jsonl", bytes: 1000 },
        ])
      if (input.endsWith("/records/0")) return Response.json(record)
      if (input.endsWith("/records/1")) return Response.json(second)
      return Response.json({
        name: "saudi_hybrid_pilot_v1.jsonl",
        count: 2,
        filtered: 2,
        page: 0,
        page_size: 100,
        domains: { writing: 2 },
        rows: [row, { ...row, id: 1, request: "Second request" }],
      })
    })
    vi.stubGlobal("fetch", fetcher)
    render(
      <ThemeProvider>
        <App />
      </ThemeProvider>
    )
    await screen.findByText("هذه رسالة مناسبة.")
    await waitFor(() =>
      expect(
        resources.peek("/api/datasets/saudi_hybrid_pilot_v1.jsonl/records/1", 0)
          ?.value
      ).toBeDefined()
    )
    fireEvent.click(
      screen.getByRole("button", { name: "Library", exact: true })
    )
    fireEvent.click(screen.getByRole("button", { name: /Second request/ }))
    expect(screen.getByText("Second response")).toBeVisible()
    expect(screen.queryByText("هذه رسالة مناسبة.")).not.toBeInTheDocument()
    expect(
      screen.queryByText("Loading conversation 2…")
    ).not.toBeInTheDocument()
    expect(
      document.querySelector('.conversation-panel [data-slot="skeleton"]')
    ).toBeNull()
    expect(
      fetcher.mock.calls.filter(([url]) => url.endsWith("/records/1"))
    ).toHaveLength(1)
    fireEvent.click(
      screen.getByRole("button", { name: "Previous conversation" })
    )
    expect(screen.getByText("هذه رسالة مناسبة.")).toBeVisible()
    expect(screen.queryByText("Second response")).not.toBeInTheDocument()
  })

  it("loads Arabic, compares variants, saves a whole review and opens a message review", async () => {
    mockApi()
    const user = userEvent.setup()
    render(
      <ThemeProvider defaultTheme="light">
        <App />
      </ThemeProvider>
    )
    expect(await screen.findByText("هذه رسالة مناسبة.")).toBeVisible()
    expect(screen.getByText("تقدر تعدلها").closest("[dir]")).toHaveAttribute(
      "dir",
      "auto"
    )
    await user.click(screen.getByRole("tab", { name: /Compare/ }))
    expect(await screen.findByText("مسودة أصلية")).toBeVisible()
    expect(screen.getByText("إجابة محسنة أطول")).toBeVisible()
    await user.click(
      screen.getByRole("button", { name: "Review", exact: true })
    )
    await user.click(screen.getByRole("radio", { name: "Good", exact: true }))
    await user.type(screen.getByLabelText("Notes"), "جميل")
    const whole = readAnnotations().entries[0]
    expect(whole.target).toBe("conversation")
    expect(whole.notes).toBe("جميل")
    expect(whole.verdict).toBe("good")
    expect(whole.record_sha256).toBe(await fingerprint(record))
    await user.click(
      screen.getByRole("tab", { name: "Conversation", exact: true })
    )
    await user.click(screen.getByRole("button", { name: /Review message 2/ }))
    expect(
      screen.getByRole("combobox", { name: "Review scope" })
    ).toHaveTextContent("Message 2")
    await user.click(
      screen.getByRole("radio", { name: "Needs work", exact: true })
    )
    expect(readAnnotations().entries).toHaveLength(2)
    expect(readAnnotations().entries.find((e) => e.target === 1)?.verdict).toBe(
      "needs_work"
    )
    expect(
      readAnnotations().entries.find((e) => e.target === "conversation")
        ?.verdict
    ).toBe("good")
  })
  it("filters the library and handles an empty result", async () => {
    mockApi()
    render(
      <ThemeProvider>
        <App />
      </ThemeProvider>
    )
    await screen.findByText("هذه رسالة مناسبة.")
    fireEvent.click(
      screen.getByRole("button", { name: "Library", exact: true })
    )
    fireEvent.change(screen.getByLabelText("Search requests or topics"), {
      target: { value: "missing" },
    })
    expect(await screen.findByText("No matches")).toBeVisible()
    await waitFor(() =>
      expect(screen.queryByText("هذه رسالة مناسبة.")).not.toBeInTheDocument()
    )
  })
  it("shows a connection error with a retry action", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("VM disconnected"))
    )
    render(
      <ThemeProvider>
        <App />
      </ThemeProvider>
    )
    expect(await screen.findByText("VM disconnected")).toBeVisible()
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled()
  })
})
