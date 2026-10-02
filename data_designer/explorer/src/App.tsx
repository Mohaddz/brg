import { useDeferredValue, useEffect, useRef, useState } from "react"
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  ArrowLeft,
  ArrowRight,
  CheckCheck,
  CircleDashed,
  Flag,
  Layers,
  MessageSquare,
  Moon,
  PanelLeft,
  PanelRight,
  RefreshCw,
  Search,
  Sun,
} from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { useTheme } from "@/components/theme-provider"
import { batchLabel, type Batch, type RecordData } from "@/lib/data"
import { resources, type ResourceResult } from "@/lib/resources"
import {
  fingerprint,
  mergeAnnotations,
  readAnnotations,
  saveAnnotations,
  type Annotation,
} from "@/lib/annotations"
import { cn } from "@/lib/utils"
import {
  Blank,
  Comparison,
  Details,
  IconButton,
  ReviewPanel,
  Screening,
  Transcript,
} from "@/components/workspace"

function useResource<T>(
  url: string | null,
  refresh: number,
  transform?: (value: T) => Promise<T>
) {
  const [result, setResult] = useState<ResourceResult<T>>()
  const transformRef = useRef(transform)
  useEffect(() => {
    transformRef.current = transform
  }, [transform])
  useEffect(() => {
    if (!url) return
    let active = true
    resources
      .load<T>(url, refresh, transformRef.current)
      .then((value) => {
        if (active) setResult(value)
      })
      .catch((error) => {
        if (active) setResult({ url, refresh, error: error.message })
      })
    return () => {
      active = false
    }
  }, [url, refresh])
  return result?.url === url && result?.refresh === refresh
    ? result
    : resources.peek<T>(url, refresh)
}

type LoadedRecord = RecordData & { _hash?: string }
async function hashRecord(record: LoadedRecord): Promise<LoadedRecord> {
  return { ...record, _hash: await fingerprint(record) }
}

export default function App() {
  const { theme, setTheme } = useTheme()
  const [refresh, setRefresh] = useState(0)
  const [choice, setChoice] = useState(
    new URLSearchParams(location.search).get("dataset") ?? ""
  )
  const [selected, setSelected] = useState(
    Number(new URLSearchParams(location.search).get("row") ?? 1) - 1
  )
  const [search, setSearch] = useState("")
  const deferredSearch = useDeferredValue(search)
  const [status, setStatus] = useState("all")
  const [domain, setDomain] = useState("all")
  const [page, setPage] = useState(0)
  const [tab, setTab] = useState("conversation")
  const [libraryOpen, setLibraryOpen] = useState(
    () => window.matchMedia("(min-width: 701px)").matches
  )
  const [reviewOpen, setReviewOpen] = useState(false)
  const [reviewScope, setReviewScope] = useState<number | undefined>()
  const [reviewRevision, setReviewRevision] = useState(0)
  const [storage, setStorage] = useState(readAnnotations)
  const importRef = useRef<HTMLInputElement>(null)
  const datasetsResult = useResource<{ name: string; bytes: number }[]>(
    "/api/datasets",
    refresh
  )
  const datasets = datasetsResult?.value
  const dataset =
    choice ||
    datasets?.find((d) => d.name === "saudi_diversity_v3_200_reviewed.jsonl")
      ?.name ||
    datasets?.find((d) => d.name === "saudi_natural_v2_50_selected.jsonl")
      ?.name ||
    datasets?.find((d) => d.name === "saudi_hybrid_pilot_v1.jsonl")?.name ||
    datasets?.[0]?.name ||
    ""
  const batchResult = useResource<Batch>(
    dataset
      ? `/api/datasets/${encodeURIComponent(dataset)}?${new URLSearchParams({ search: deferredSearch, status, domain, page: String(page) })}`
      : null,
    refresh
  )
  const batch = batchResult?.value
  const selectedRow =
    batch?.rows.find((row) => row.id === selected) ?? batch?.rows[0]
  const recordResult = useResource<LoadedRecord>(
    dataset && selectedRow
      ? `/api/datasets/${encodeURIComponent(dataset)}/records/${selectedRow.id}`
      : null,
    refresh,
    hashRecord
  )
  const record = recordResult?.value
  const prefetchRecord = (id: number) => {
    if (dataset)
      void resources
        .load<LoadedRecord>(
          `/api/datasets/${encodeURIComponent(dataset)}/records/${id}`,
          refresh,
          hashRecord
        )
        .catch(() => {
          /* The visible request reports failures; prefetch is optional. */
        })
  }
  useEffect(() => {
    if (!record || !batch || !selectedRow) return
    const position = batch.rows.findIndex((row) => row.id === selectedRow.id)
    for (const row of [batch.rows[position - 1], batch.rows[position + 1]]) {
      if (row)
        void resources
          .load<LoadedRecord>(
            `/api/datasets/${encodeURIComponent(dataset)}/records/${row.id}`,
            refresh,
            hashRecord
          )
          .catch(() => {})
    }
  }, [record, batch, selectedRow, dataset, refresh])
  const error =
    datasetsResult?.error || batchResult?.error || recordResult?.error
  const currentEntries = storage.entries.filter((e) => e.dataset === dataset)
  const reviewed = new Set(
    currentEntries
      .filter((e) => e.target === "conversation" && e.verdict !== "unrated")
      .map((e) => e.record_sha256)
  ).size
  useEffect(() => {
    if (dataset && selectedRow)
      history.replaceState(
        null,
        "",
        `?${new URLSearchParams({ dataset, row: String(selectedRow.id + 1) })}`
      )
  }, [dataset, selectedRow])
  function chooseRow(id: number) {
    setSelected(id)
    setReviewScope(undefined)
    if (window.matchMedia("(max-width: 700px)").matches) {
      setLibraryOpen(false)
      setReviewOpen(false)
    }
  }
  function update(entry: Annotation) {
    if (storage.error) return false
    try {
      const entries = mergeAnnotations(storage.entries, [entry])
      saveAnnotations(entries)
      setStorage({ entries, error: "" })
      return true
    } catch {
      toast.error(
        "Could not save review. Export a backup and check browser storage."
      )
      return false
    }
  }
  async function importFile(file?: File) {
    if (!file) return
    try {
      const text = await file.text()
      const imported = text
        .split(/\r?\n/)
        .filter((line) => line.trim())
        .map((line) => JSON.parse(line))
      const entries = mergeAnnotations(storage.entries, imported)
      saveAnnotations(entries)
      setStorage({ entries, error: "" })
      setReviewRevision((v) => v + 1)
      toast.success(`Imported ${imported.length} reviews`)
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Could not import annotations"
      )
    }
    if (importRef.current) importRef.current.value = ""
  }
  function exportReviews() {
    if (storage.error) {
      toast.error(storage.error)
      return
    }
    const blob = new Blob(
      [storage.entries.map((e) => JSON.stringify(e)).join("\n") + "\n"],
      { type: "application/x-ndjson" }
    )
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = "brg-explorer.annotations.jsonl"
    link.click()
    URL.revokeObjectURL(url)
    toast.success(`Exported ${storage.entries.length} reviews`)
  }
  const position =
    batch?.rows.findIndex((row) => row.id === selectedRow?.id) ?? -1
  return (
    <TooltipProvider>
      <div className="app-shell">
        <header className="topbar">
          <a href="/" className="brand">
            <span className="brand-mark">
              <Layers className="size-5" />
            </span>
            <span>
              BRG
              <span className="font-normal text-muted-foreground">
                {" "}
                / explorer
              </span>
            </span>
          </a>
          <Button
            variant="ghost"
            size="sm"
            aria-expanded={libraryOpen}
            aria-controls="library-panel"
            onClick={() => {
              setLibraryOpen((open) => !open)
              if (window.matchMedia("(max-width: 700px)").matches)
                setReviewOpen(false)
            }}
          >
            <PanelLeft data-icon="inline-start" />
            Library
          </Button>
          <span className="topbar-caption">
            {batch?.count ?? "—"} chats · {batch?.median_words ?? "—"} median
            words · {reviewed} reviewed
          </span>
          <div className="ml-auto flex items-center gap-2">
            <Button
              variant={reviewOpen ? "secondary" : "ghost"}
              size="sm"
              aria-expanded={reviewOpen}
              aria-controls="review-anchor"
              onClick={() => {
                setReviewOpen((open) => !open)
                if (window.matchMedia("(max-width: 700px)").matches)
                  setLibraryOpen(false)
              }}
            >
              <PanelRight data-icon="inline-start" />
              Review
            </Button>
            <IconButton
              label="Refresh datasets"
              onClick={() => setRefresh((v) => v + 1)}
            >
              <RefreshCw />
            </IconButton>
            <IconButton
              label="Toggle theme"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? <Sun /> : <Moon />}
            </IconButton>
            <Button
              variant="outline"
              size="sm"
              aria-label="Import reviews"
              onClick={() => importRef.current?.click()}
            >
              <ArrowUpFromLine data-icon="inline-start" />
              <span className="action-label">Import reviews</span>
            </Button>
            <Button
              size="sm"
              onClick={exportReviews}
              disabled={!storage.entries.length || Boolean(storage.error)}
              aria-label="Export reviews"
            >
              <ArrowDownToLine data-icon="inline-start" />
              <span className="action-label">Export reviews</span>
            </Button>
            <input
              ref={importRef}
              type="file"
              accept=".jsonl,.ndjson"
              className="hidden"
              aria-label="Import annotations file"
              onChange={(e) => void importFile(e.target.files?.[0])}
            />
          </div>
        </header>
        <main className="main-shell">
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertTitle>Could not load the workspace</AlertTitle>
              <AlertDescription>
                {error}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setRefresh((v) => v + 1)}
                >
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          )}
          {batch?.malformed ? (
            <Alert className="mb-4">
              <AlertTitle>Some rows could not be read</AlertTitle>
              <AlertDescription>
                {batch.malformed} malformed rows were skipped.
              </AlertDescription>
            </Alert>
          ) : null}
          <div
            className="workspace"
            data-library-open={libraryOpen}
            data-review-open={reviewOpen}
          >
            <aside
              id="library-panel"
              className="library-panel"
              aria-label="Conversation library"
              hidden={!libraryOpen}
            >
              <div className="library-controls">
                <div className="flex items-center justify-between">
                  <h2>Library</h2>
                  <Badge variant="secondary">{batch?.filtered ?? "—"}</Badge>
                </div>
                <FieldGroup>
                  <Field>
                    <FieldLabel className="sr-only">Dataset</FieldLabel>
                    <Select
                      value={dataset || undefined}
                      onValueChange={(v) => {
                        setChoice(v)
                        setSelected(0)
                        setPage(0)
                        setDomain("all")
                        setSearch("")
                        setReviewScope(undefined)
                      }}
                    >
                      <SelectTrigger className="w-full" aria-label="Dataset">
                        <SelectValue placeholder="Select a dataset" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          {datasets?.map((d) => (
                            <SelectItem key={d.name} value={d.name}>
                              {batchLabel(d.name)}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </Field>
                  <Field>
                    <FieldLabel className="sr-only" htmlFor="search">
                      Search requests or topics
                    </FieldLabel>
                    <InputGroup>
                      <InputGroupAddon>
                        <Search />
                      </InputGroupAddon>
                      <InputGroupInput
                        id="search"
                        placeholder="Search requests or topics…"
                        value={search}
                        onChange={(e) => {
                          setSearch(e.target.value)
                          setPage(0)
                        }}
                      />
                    </InputGroup>
                  </Field>
                  <Field>
                    <FieldLabel className="sr-only">Machine status</FieldLabel>
                    <ToggleGroup
                      type="single"
                      variant="outline"
                      value={status}
                      onValueChange={(v) => {
                        if (v) {
                          setStatus(v)
                          setPage(0)
                        }
                      }}
                      className="w-full"
                    >
                      <ToggleGroupItem value="all">All</ToggleGroupItem>
                      <ToggleGroupItem value="pass">Pass</ToggleGroupItem>
                      <ToggleGroupItem value="flagged">Flagged</ToggleGroupItem>
                    </ToggleGroup>
                  </Field>
                  <Field>
                    <FieldLabel className="sr-only">Topic</FieldLabel>
                    <Select
                      value={domain}
                      onValueChange={(v) => {
                        setDomain(v)
                        setPage(0)
                      }}
                    >
                      <SelectTrigger aria-label="Topic">
                        <SelectValue placeholder="All topics" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          <SelectItem value="all">All topics</SelectItem>
                          {Object.entries(batch?.domains ?? {}).map(
                            ([name, count]) => (
                              <SelectItem key={name} value={name}>
                                {name} · {count}
                              </SelectItem>
                            )
                          )}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </Field>
                </FieldGroup>
              </div>
              <Separator />
              <div className="conversation-list">
                {!datasetsResult ? (
                  <LoadingRows />
                ) : datasets?.length === 0 ? (
                  <Blank
                    title="No datasets yet"
                    description="Finished JSONL batches in the VM output folder appear here."
                  />
                ) : !batch && !error ? (
                  <LoadingRows />
                ) : !batch?.rows.length ? (
                  <Blank
                    title="No matches"
                    description="Try another topic or a shorter search."
                  />
                ) : (
                  batch.rows.map((row) => (
                    <button
                      key={row.id}
                      className={cn(
                        "conversation-row",
                        row.id === selectedRow?.id && "is-selected"
                      )}
                      aria-current={
                        row.id === selectedRow?.id ? "true" : undefined
                      }
                      onClick={() => chooseRow(row.id)}
                      onPointerEnter={() => prefetchRecord(row.id)}
                      onFocus={() => prefetchRecord(row.id)}
                    >
                      <div className="row-meta">
                        <span className="row-number">
                          {String(row.id + 1).padStart(2, "0")}
                        </span>
                        <span className="capitalize">{row.domain}</span>
                        {row.passed === true ? (
                          <CheckCheck
                            className="ml-auto size-3.5 text-primary"
                            aria-label="Machine pass"
                          />
                        ) : row.passed === false ? (
                          <Flag
                            className="ml-auto size-3.5 text-muted-foreground"
                            aria-label="Machine flagged"
                          />
                        ) : (
                          <CircleDashed className="ml-auto size-3.5" />
                        )}
                      </div>
                      <p dir="auto">
                        {row.request || row.scenario || "Untitled conversation"}
                      </p>
                      <div className="row-bottom">
                        <span>
                          {row.exchanges}{" "}
                          {row.exchanges === 1 ? "exchange" : "exchanges"}
                        </span>
                        <span>{row.words} words</span>
                      </div>
                    </button>
                  ))
                )}
              </div>
              <Separator />
              <div className="library-footer">
                <span>{batch?.filtered ?? 0} results</span>
                <div className="flex gap-1">
                  <IconButton
                    label="Previous page"
                    disabled={page === 0}
                    onClick={() => setPage((v) => v - 1)}
                  >
                    <ArrowLeft />
                  </IconButton>
                  <IconButton
                    label="Next page"
                    disabled={
                      !batch || (page + 1) * batch.page_size >= batch.filtered
                    }
                    onClick={() => setPage((v) => v + 1)}
                  >
                    <ArrowRight />
                  </IconButton>
                </div>
              </div>
            </aside>
            <section
              className="conversation-panel"
              aria-label="Selected conversation"
            >
              {record && selectedRow ? (
                <>
                  <div className="conversation-heading">
                    <div className="flex flex-col gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="eyebrow">
                          CONVERSATION{" "}
                          {String(selectedRow.id + 1).padStart(2, "0")}
                        </span>
                        <Badge variant="outline">{selectedRow.domain}</Badge>
                        <Badge
                          variant={
                            record.screening_passed === true
                              ? "secondary"
                              : "outline"
                          }
                        >
                          {record.screening_scope && "Original "}
                          {record.screening_passed === true
                            ? "Machine pass"
                            : record.screening_passed === false
                              ? "Machine flagged"
                              : "Unscreened"}
                        </Badge>
                        {record.agent_review?.verdict === "pass" && (
                          <Badge variant="secondary">
                            {record.qa_repair
                              ? "Corrected · agent checked"
                              : "Agent checked"}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <IconButton
                        label="Previous conversation"
                        disabled={position <= 0}
                        onClick={() => chooseRow(batch!.rows[position - 1].id)}
                      >
                        <ArrowLeft />
                      </IconButton>
                      <IconButton
                        label="Next conversation"
                        disabled={!batch || position >= batch.rows.length - 1}
                        onClick={() => chooseRow(batch!.rows[position + 1].id)}
                      >
                        <ArrowRight />
                      </IconButton>
                    </div>
                  </div>
                  <Tabs
                    value={tab}
                    onValueChange={setTab}
                    className="conversation-tabs"
                  >
                    <div className="tab-bar">
                      <TabsList variant="line">
                        <TabsTrigger value="conversation">
                          <MessageSquare />
                          Conversation
                        </TabsTrigger>
                        <TabsTrigger value="compare">
                          <Layers />
                          Compare
                        </TabsTrigger>
                        <TabsTrigger value="screening">
                          <Flag />
                          Screening
                        </TabsTrigger>
                        <TabsTrigger value="details">Details</TabsTrigger>
                      </TabsList>
                    </div>
                    <TabsContent
                      value="conversation"
                      className="transcript-tab"
                    >
                      <Transcript
                        key={record._hash}
                        record={record}
                        onReview={(i) => {
                          setReviewScope(i)
                          setReviewOpen(true)
                          if (window.matchMedia("(max-width: 700px)").matches)
                            setLibraryOpen(false)
                        }}
                      />
                    </TabsContent>
                    <TabsContent value="compare">
                      <Comparison record={record} />
                    </TabsContent>
                    <TabsContent value="screening">
                      <Screening record={record} />
                    </TabsContent>
                    <TabsContent value="details">
                      <Details record={record} cost={batch?.cost} />
                    </TabsContent>
                  </Tabs>
                </>
              ) : !error && selectedRow ? (
                <p role="status" className="p-6 text-sm text-muted-foreground">
                  Loading conversation {selectedRow.id + 1}…
                </p>
              ) : (
                <Blank
                  title="A conversation worth reading"
                  description="Select an exchange from the library to explore its responses."
                />
              )}
            </section>
            <div id="review-anchor" hidden={!reviewOpen}>
              {record && selectedRow ? (
                <ReviewPanel
                  key={record._hash + ":" + reviewRevision + ":" + reviewScope}
                  initialTarget={reviewScope}
                  record={record}
                  dataset={dataset}
                  row={selectedRow.id}
                  hash={record._hash!}
                  entries={storage.entries}
                  blocked={storage.error}
                  update={update}
                />
              ) : (
                <aside className="review-panel">
                  <Blank
                    title="Your perspective matters"
                    description="Open a conversation to review its quality."
                  />
                </aside>
              )}
            </div>
          </div>
        </main>
      </div>
      <Toaster />
    </TooltipProvider>
  )
}

function LoadingRows() {
  return (
    <p role="status" className="p-4 text-sm text-muted-foreground">
      Loading conversations…
    </p>
  )
}
