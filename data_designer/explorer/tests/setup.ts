import "@testing-library/jest-dom/vitest"
import { afterEach, vi } from "vitest"
import { cleanup } from "@testing-library/react"
import { webcrypto } from "node:crypto"
Object.defineProperty(globalThis, "crypto", { value: webcrypto })
class Observer {
  observe() {}
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal("ResizeObserver", Observer)
vi.stubGlobal("IntersectionObserver", Observer)
Object.defineProperty(window, "matchMedia", {
  value: () => ({
    matches: false,
    addEventListener() {},
    removeEventListener() {},
  }),
})
HTMLElement.prototype.scrollIntoView = vi.fn()
HTMLElement.prototype.scrollTo = vi.fn()
HTMLElement.prototype.hasPointerCapture = () => false
HTMLElement.prototype.setPointerCapture = () => {}
HTMLElement.prototype.releasePointerCapture = () => {}
afterEach(() => {
  cleanup()
  localStorage.clear()
  vi.restoreAllMocks()
})
