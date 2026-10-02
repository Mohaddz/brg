import { afterEach, describe, expect, it, vi } from "vitest"
import { ResourceCache } from "../src/lib/resources"

afterEach(() => vi.unstubAllGlobals())

describe("conversation resource cache", () => {
  it("shares prefetch with the reader and caches the transformed fingerprint", async () => {
    const fetcher = vi.fn(
      async () => new Response(JSON.stringify({ content: "chat" }))
    )
    vi.stubGlobal("fetch", fetcher)
    const transform = vi.fn(
      async (record: { content: string; hash?: string }) => ({
        ...record,
        hash: "checked",
      })
    )
    const cache = new ResourceCache()
    const first = cache.load("/records/1", 0, transform)
    const second = cache.load("/records/1", 0, transform)
    expect(second).toBe(first)
    await second
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(transform).toHaveBeenCalledTimes(1)
    expect(cache.peek("/records/1", 0)?.value).toEqual({
      content: "chat",
      hash: "checked",
    })
  })

  it("keeps rows separate even when responses arrive out of order", async () => {
    let finishFirst!: (response: Response) => void
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        url.endsWith("/1")
          ? new Promise<Response>((resolve) => {
              finishFirst = resolve
            })
          : Promise.resolve(new Response(JSON.stringify({ row: 2 })))
      )
    )
    const cache = new ResourceCache()
    const first = cache.load("/records/1", 0)
    await cache.load("/records/2", 0)
    finishFirst(new Response(JSON.stringify({ row: 1 })))
    await first
    expect(cache.peek("/records/1", 0)?.value).toEqual({ row: 1 })
    expect(cache.peek("/records/2", 0)?.value).toEqual({ row: 2 })
  })

  it("refresh ignores cached content and retrieves a new version", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ version: 1 })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ version: 2 })))
    vi.stubGlobal("fetch", fetcher)
    const cache = new ResourceCache()
    await cache.load("/records/1", 0)
    expect(cache.peek("/records/1", 1)).toBeUndefined()
    await cache.load("/records/1", 1)
    expect(cache.peek("/records/1", 1)?.value).toEqual({ version: 2 })
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it("bounds retained data instead of accumulating every visited chat", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}"))
    )
    const cache = new ResourceCache(2)
    for (const id of [1, 2, 3]) await cache.load(`/records/${id}`, 0)
    expect(cache.peek("/records/1", 0)).toBeUndefined()
    expect(cache.peek("/records/2", 0)).toBeDefined()
    expect(cache.peek("/records/3", 0)).toBeDefined()
  })

  it("allows retry after a failed prefetch", async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(new Response("{}"))
    vi.stubGlobal("fetch", fetcher)
    const cache = new ResourceCache()
    await expect(cache.load("/records/1", 0)).rejects.toThrow("offline")
    await expect(cache.load("/records/1", 0)).resolves.toMatchObject({
      value: {},
    })
    expect(fetcher).toHaveBeenCalledTimes(2)
  })
})
