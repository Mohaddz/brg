import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { Details, Screening } from "../src/components/workspace"

describe("lightweight pilot review", () => {
  it("shows conversation ratings without draft/enhancement claims", () => {
    render(<Screening record={{ recipe_version: "saudi-lightweight-v1", screening_passed: true,
      selective_review: { acceptable: true, accuracy: 5, usefulness: 4, naturalness: 4,
        continuity: 5, baseline_comparison: "similar", issues: [], reason: "Useful connected follow-ups" },
      turn_reviews: [{ turn: 0, review: {}, issues: [] }], repair_count: 1 }} />)
    expect(screen.getByText("Accuracy 5/5")).toBeInTheDocument()
    expect(screen.getByText("First answer: similar to baseline")).toBeInTheDocument()
    expect(screen.queryByText(/Draft completeness/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Enhancement adds value/)).not.toBeInTheDocument()
  })

  it("shows provider cost instead of an unrelated key delta", () => {
    render(<Details record={{}} cost={{ reported_cost_usd: "0.02", observed_key_usage_delta_usd: "0.08" }} />)
    expect(screen.getByText("$0.0200")).toBeInTheDocument()
    expect(screen.queryByText("$0.0800")).not.toBeInTheDocument()
  })
})
