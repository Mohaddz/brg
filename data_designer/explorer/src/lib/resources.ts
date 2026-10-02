import { api } from "./data"

export type ResourceResult<T> = {
  url: string
  refresh: number
  value?: T
  error?: string
}

/** Bounded, session-only cache; refresh creates a new request namespace. */
export class ResourceCache {
  private entries = new Map<
    string,
    {
      result?: ResourceResult<unknown>
      pending: Promise<ResourceResult<unknown>>
    }
  >()

  private capacity: number
  constructor(capacity = 48) {
    this.capacity = capacity
  }

  clear() {
    this.entries.clear()
  }

  peek<T>(url: string | null, refresh: number) {
    return url
      ? (this.entries.get(JSON.stringify([refresh, url]))?.result as
          ResourceResult<T> | undefined)
      : undefined
  }

  load<T>(
    url: string,
    refresh: number,
    transform?: (value: T) => Promise<T>
  ): Promise<ResourceResult<T>> {
    const key = JSON.stringify([refresh, url])
    const existing = this.entries.get(key)
    if (existing) return existing.pending as Promise<ResourceResult<T>>
    const entry = { pending: Promise.resolve({ url, refresh }) } as {
      result?: ResourceResult<unknown>
      pending: Promise<ResourceResult<unknown>>
    }
    entry.pending = api<T>(url)
      .then((value) => (transform ? transform(value) : value))
      .then((value) => {
        const result = { url, refresh, value }
        entry.result = result
        return result
      })
      .catch((error) => {
        if (this.entries.get(key) === entry) this.entries.delete(key)
        throw error
      })
    this.entries.set(key, entry)
    while (this.entries.size > this.capacity)
      this.entries.delete(this.entries.keys().next().value!)
    return entry.pending as Promise<ResourceResult<T>>
  }
}

export const resources = new ResourceCache()
