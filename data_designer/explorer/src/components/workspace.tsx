import { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import {
  Check,
  CheckCheck,
  ChevronRight,
  CircleDashed,
  Copy,
  Database,
  Flag,
  Layers,
  MessageSquare,
  Sparkles,
  X,
} from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Message,
  MessageContent,
  MessageFooter,
  MessageHeader,
} from "@/components/ui/message"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
import {
  MessageScroller,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller"
import { getMessages, wordCount, type RecordData, type Batch } from "@/lib/data"
import { issues, type Annotation, type Verdict } from "@/lib/annotations"
import { cn } from "@/lib/utils"

export function Markdown({ text }: { text: string }) {
  return (
    <div className="markdown" dir="auto">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre: ({ children }) => <pre dir="ltr">{children}</pre>,
          a: ({ children, ...props }) => (
            <a {...props} target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  )
}
export function IconButton({
  label,
  children,
  onClick,
  disabled,
}: {
  label: string
  children: React.ReactNode
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={label}
          onClick={onClick}
          disabled={disabled}
        >
          {children}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}
export function Blank({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <MessageSquare />
        </EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
    </Empty>
  )
}
export function ReviewPanel({
  record,
  dataset,
  row,
  hash,
  entries,
  blocked,
  update,
  initialTarget,
}: {
  record: RecordData
  dataset: string
  row: number
  hash: string
  entries: Annotation[]
  blocked: string
  update: (entry: Annotation) => boolean
  initialTarget?: number
}) {
  const [target, setTarget] = useState<"conversation" | number>(
    initialTarget !== undefined &&
      initialTarget >= 0 &&
      initialTarget < getMessages(record).length
      ? initialTarget
      : "conversation"
  )
  const existing = entries.find(
    (e) =>
      e.dataset === dataset && e.record_sha256 === hash && e.target === target
  )
  return (
    <aside className="review-panel" aria-label="Human review">
      <div className="panel-heading">
        <div>
          <h2>Your review</h2>
          <p>Decide what belongs in training.</p>
        </div>
        <CheckCheck className="size-5 text-primary" />
      </div>
      <Separator />
      <FieldGroup className="p-5">
        <Field>
          <FieldLabel>Review scope</FieldLabel>
          <Select
            value={String(target)}
            onValueChange={(v) =>
              setTarget(v === "conversation" ? v : Number(v))
            }
          >
            <SelectTrigger aria-label="Review scope">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="conversation">Whole conversation</SelectItem>
                {getMessages(record).map((m, i) => (
                  <SelectItem key={i} value={String(i)}>
                    Message {i + 1} · {m.role}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
        <ReviewFields
          key={hash + ":" + target}
          existing={existing}
          blocked={blocked}
          onChange={(values) =>
            update({
              schema_version: 1,
              dataset,
              record_sha256: hash,
              target,
              row: row + 1,
              seed_index: record.seed_index,
              topic: record.domain ?? record.subject,
              recipe_version: record.recipe_version,
              messages: getMessages(record),
              ...values,
              updated_at: new Date().toISOString(),
            })
          }
        />
      </FieldGroup>
      <Separator />
      <div className="flex flex-col gap-4 p-5">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Database className="size-3.5" />
          Saved in this browser · export a backup
        </div>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Machine screening is a suggestion. Training export still requires an
          explicit good review and a machine pass.
        </p>
        <div className="flex flex-col gap-2 text-xs">
          <span className="eyebrow">RECIPE</span>
          <span>{record.recipe_version ?? "Not specified"}</span>
          <span className="eyebrow mt-2">RESPONSE DEPTH</span>
          <span className="capitalize">
            {record.depth ?? record.profile ?? "Not specified"}
          </span>
          <span className="eyebrow mt-2">WRITER</span>
          <span className="break-all text-muted-foreground">
            {record.writer_model ?? "Not specified"}
          </span>
        </div>
      </div>
    </aside>
  )
}
function ReviewFields({
  existing,
  blocked,
  onChange,
}: {
  existing?: Annotation
  blocked: string
  onChange: (
    values: Pick<Annotation, "verdict" | "issues" | "notes">
  ) => boolean
}) {
  const [values, setValues] = useState({
    verdict: existing?.verdict ?? ("unrated" as Verdict),
    issues: existing?.issues ?? [],
    notes: existing?.notes ?? "",
  })
  const [saved, setSaved] = useState(Boolean(existing))
  function change(next: typeof values) {
    if (onChange(next)) {
      setValues(next)
      setSaved(true)
    }
  }
  return (
    <>
      {blocked && (
        <Alert variant="destructive">
          <AlertTitle>Review paused</AlertTitle>
          <AlertDescription>{blocked}</AlertDescription>
        </Alert>
      )}
      <Field>
        <FieldLabel>Human verdict</FieldLabel>
        <ToggleGroup
          type="single"
          variant="outline"
          value={values.verdict}
          disabled={Boolean(blocked)}
          onValueChange={(v) => {
            if (v) change({ ...values, verdict: v as Verdict })
          }}
          className="review-verdict"
        >
          <ToggleGroupItem value="good" aria-label="Good">
            <Check />
            Good
          </ToggleGroupItem>
          <ToggleGroupItem value="needs_work" aria-label="Needs work">
            <Flag />
            Needs work
          </ToggleGroupItem>
          <ToggleGroupItem value="reject" aria-label="Reject">
            <X />
            Reject
          </ToggleGroupItem>
        </ToggleGroup>
      </Field>
      <Field>
        <FieldLabel>What needs attention?</FieldLabel>
        <ToggleGroup
          type="multiple"
          variant="outline"
          value={values.issues}
          disabled={Boolean(blocked)}
          onValueChange={(v) => change({ ...values, issues: v })}
          className="issue-tags"
          aria-label="Review issues"
        >
          {issues.map((issue) => (
            <ToggleGroupItem key={issue} value={issue}>
              {issue.replace(/_/g, " ")}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </Field>
      <Field>
        <FieldLabel htmlFor="review-notes">Notes</FieldLabel>
        <Textarea
          id="review-notes"
          dir="auto"
          placeholder="What would make this response better?"
          rows={5}
          disabled={Boolean(blocked)}
          value={values.notes}
          onChange={(e) => change({ ...values, notes: e.target.value })}
        />
        <FieldDescription aria-live="polite">
          {saved ? "Saved locally" : "Changes save automatically"}
        </FieldDescription>
      </Field>
      {saved && (
        <Button
          variant="ghost"
          size="sm"
          disabled={Boolean(blocked)}
          onClick={() => change({ verdict: "unrated", issues: [], notes: "" })}
        >
          <CircleDashed data-icon="inline-start" />
          Reset this review
        </Button>
      )}
    </>
  )
}
export function Transcript({
  record,
  onReview,
}: {
  record: RecordData
  onReview: (index: number) => void
}) {
  return (
    <MessageScrollerProvider defaultScrollPosition="start" autoScroll={false}>
      <MessageScroller>
        <MessageScrollerViewport aria-label="Conversation transcript">
          <MessageScrollerContent className="transcript">
            {getMessages(record).map((message, i) => (
              <MessageScrollerItem key={i} messageId={String(i)}>
                <Message align={message.role === "user" ? "end" : "start"}>
                  <MessageContent>
                    <MessageHeader className="gap-2">
                      {message.role === "assistant" ? (
                        <Sparkles />
                      ) : (
                        <MessageSquare />
                      )}
                      <span>
                        {message.role === "assistant"
                          ? "Assistant"
                          : message.role === "user"
                            ? "User"
                            : message.role}
                      </span>
                      <span className="ml-auto">
                        {wordCount(message.content)} words
                      </span>
                    </MessageHeader>
                    <Bubble
                      variant={message.role === "user" ? "tinted" : "ghost"}
                      className={cn(message.role === "assistant" && "w-full")}
                    >
                      <BubbleContent>
                        <Markdown text={message.content} />
                      </BubbleContent>
                    </Bubble>
                    <MessageFooter className="gap-2">
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={() => onReview(i)}
                      >
                        Review message {i + 1}
                        <ChevronRight data-icon="inline-end" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        aria-label={`Copy message ${i + 1}`}
                        onClick={() =>
                          navigator.clipboard
                            .writeText(message.content)
                            .then(() => toast.success("Message copied"))
                            .catch(() => toast.error("Could not copy message"))
                        }
                      >
                        <Copy />
                      </Button>
                    </MessageFooter>
                  </MessageContent>
                </Message>
              </MessageScrollerItem>
            ))}
          </MessageScrollerContent>
        </MessageScrollerViewport>
      </MessageScroller>
    </MessageScrollerProvider>
  )
}
export function Comparison({ record }: { record: RecordData }) {
  if (!record.answer_variants?.length)
    return (
      <Blank
        title="No variants in this batch"
        description="This conversation contains only the selected response."
      />
    )
  return (
    <div className="detail-scroll">
      <div className="flex flex-col gap-8 p-6">
        {record.answer_variants.map((v) => (
          <section key={v.turn} className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="eyebrow">EXCHANGE {v.turn}</span>
              <Badge variant="secondary">Selected: {v.selected}</Badge>
            </div>
            <p className="request-context" dir="auto">
              {v.user}
            </p>
            <div className="compare-grid">
              {(["draft", "enhanced"] as const).map((kind) => (
                <Card key={kind} className="min-w-0">
                  <CardHeader>
                    <CardTitle>
                      <span className="flex items-center gap-2">
                        {kind === "enhanced" ? <Sparkles /> : <Layers />}
                        {kind === "enhanced" ? "Enhanced" : "Original draft"}
                      </span>
                    </CardTitle>
                    <CardDescription>
                      {wordCount(v[kind])} words
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Markdown text={v[kind]} />
                  </CardContent>
                  <CardFooter>
                    <Badge
                      variant={v.selected === kind ? "default" : "outline"}
                    >
                      {v.selected === kind
                        ? "Selected response"
                        : "Alternative"}
                    </Badge>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}
export function Screening({ record }: { record: RecordData }) {
  return (
    <div className="detail-scroll flex flex-col gap-5 p-6">
      {record.agent_review && (
        <Alert>
          <AlertTitle>Agent review: {record.agent_review.verdict}</AlertTitle>
          <AlertDescription>
            {record.agent_review.notes} Human approval is pending.
          </AlertDescription>
        </Alert>
      )}
      <Alert>
        <AlertTitle>
          {record.screening_scope && (record.agent_review || !record.recipe_version?.startsWith("saudi-lightweight")) && "Original "}
          {record.screening_passed === true
            ? "Machine screening passed"
            : record.screening_passed === false
              ? "Machine screening flagged this conversation"
              : "No machine screening available"}
        </AlertTitle>
        <AlertDescription>
          {record.screening_scope || "Use these observations to inform your review."} {record.stop_reason}
        </AlertDescription>
      </Alert>
      {record.recipe_version?.startsWith("saudi-lightweight") && (
        <Card>
          <CardHeader>
            <CardTitle>Conversation quality review</CardTitle>
            <CardDescription>
              {record.selective_review ? (record.agent_review ? "Luna screening checkpoint; current agent review above" : "Luna reviewed this complete chat") : "Code checks only; outside the model review sample"}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {record.selective_review && <>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">Accuracy {record.selective_review.accuracy}/5</Badge>
                <Badge variant="outline">Usefulness {record.selective_review.usefulness}/5</Badge>
                <Badge variant="outline">Naturalness {record.selective_review.naturalness}/5</Badge>
                <Badge variant="outline">Continuity {record.selective_review.continuity}/5</Badge>
                <Badge variant="secondary">First answer: {record.selective_review.baseline_comparison} to baseline</Badge>
              </div>
              <Markdown text={record.selective_review.reason} />
            </>}
            {!!record.remaining_issues?.length && <ul className="screening-issues" dir="auto">
              {record.remaining_issues.map((issue, index) => <li key={index}>{issue}</li>)}
            </ul>}
          </CardContent>
          <CardFooter><p className="text-xs text-muted-foreground">
            {record.repair_count ?? 0} repair calls. Model ratings are screening; human approval is pending.
          </p></CardFooter>
        </Card>
      )}
      {!record.recipe_version?.startsWith("saudi-lightweight") && record.turn_reviews?.map((item) => (
        <Card key={item.turn}>
          <CardHeader>
            <CardTitle>Exchange {item.turn}</CardTitle>
            <CardDescription>
              Model preference: {String(item.review.preferred ?? "unspecified")}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">
                Draft completeness{" "}
                {String(item.review.draft_completeness ?? "—")}/5
              </Badge>
              <Badge variant="outline">
                Enhanced completeness{" "}
                {String(item.review.enhanced_completeness ?? "—")}/5
              </Badge>
              <Badge variant="secondary">
                {item.review.enhanced_adds_value
                  ? "Enhancement adds value"
                  : "No added value"}
              </Badge>
              {item.review.unnecessary_padding === true && (
                <Badge variant="destructive">Padding detected</Badge>
              )}
            </div>
            <Markdown text={String(item.review.reason ?? "")} />
            {item.issues?.length > 0 && (
              <ul className="screening-issues" dir="auto">
                {item.issues.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            )}
          </CardContent>
          <CardFooter>
            <p className="text-xs text-muted-foreground">
              Judge: {record.judge_model ?? "unspecified"}
            </p>
          </CardFooter>
        </Card>
      ))}
    </div>
  )
}

export function Details({
  record,
  cost,
}: {
  record: RecordData
  cost?: Batch["cost"]
}) {
  const raw = { ...record } as Record<string, unknown>
  delete raw._hash
  const facts = raw.fact_pack
  const sources = raw.sources
  const show = (value: unknown) =>
    typeof value === "string" ? value : JSON.stringify(value, null, 2)
  return (
    <div className="detail-scroll flex flex-col gap-5 p-6">
      {(cost?.reported_cost_usd !== undefined || cost?.observed_key_usage_delta_usd !== undefined) && (
        <Card>
          <CardHeader>
            <CardTitle>Batch cost</CardTitle>
            <CardDescription>{cost?.reported_cost_usd !== undefined ? "Sum of provider-reported request costs" : "Observed key-level usage change"}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-medium">
              ${Number(cost?.reported_cost_usd ?? cost?.observed_key_usage_delta_usd).toFixed(4)}
            </p>
            <p className="mt-3 text-xs text-muted-foreground">
              {cost?.measurement_note ||
                "Includes concurrent activity and delayed billing; not per-request billing."}
            </p>
            {!!cost?.unresolved_request_count && <p className="mt-3 text-xs text-muted-foreground">
              {cost.unresolved_request_count} interrupted request with unconfirmed billing: at most ${Number(cost.unresolved_cost_upper_bound_usd ?? 0).toFixed(4)} additional.
            </p>}
          </CardContent>
          <CardFooter>
            <p className="text-xs text-muted-foreground">
              {cost?.completed_conversations ?? "—"} completed conversations
            </p>
          </CardFooter>
        </Card>
      )}
      {Boolean(facts) && show(facts) !== "[]" && (
        <Card>
          <CardHeader>
            <CardTitle>Source facts</CardTitle>
            <CardDescription>
              Evidence supplied to the generator
            </CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="raw-record" dir="auto">
              {show(facts)}
            </pre>
          </CardContent>
        </Card>
      )}
      {Boolean(sources) && show(sources) !== "[]" && (
        <Card>
          <CardHeader>
            <CardTitle>Provenance</CardTitle>
            <CardDescription>Source notes and references</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="raw-record" dir="auto">
              {show(sources)}
            </pre>
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader>
          <CardTitle>Full record</CardTitle>
          <CardDescription>
            Original dataset fields, including recipe and model metadata
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="raw-record" dir="ltr">
            {JSON.stringify(raw, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}
