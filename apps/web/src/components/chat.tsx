"use client";

import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, FormEvent, KeyboardEvent } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const MAX_CHARS = 4000;
const REQUEST_TIMEOUT_MS = 30_000;

const EXAMPLE_QUESTIONS = [
  "What does a blood pressure reading of 120/80 mean?",
  "What is the difference between a cold and the flu?",
];

type Citation = {
  passage_id: string;
  title: string;
  source_url: string | null;
};

type ChatApiResponse = {
  request_id: string;
  answer: string;
  citations: Citation[];
  safety_status: string;
  clarification_required: boolean;
  professional_review_recommended: boolean;
  model_id: string;
  model_revision: string;
  prompt_version: string;
  is_demo: boolean;
};

type Message =
  | { id: number; role: "user"; text: string }
  | { id: number; role: "assistant"; data: ChatApiResponse };

function isCitation(value: unknown): value is Citation {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.passage_id === "string" &&
    typeof v.title === "string" &&
    (typeof v.source_url === "string" || v.source_url === null)
  );
}

function isChatApiResponse(value: unknown): value is ChatApiResponse {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.request_id === "string" &&
    typeof v.answer === "string" &&
    Array.isArray(v.citations) &&
    typeof v.safety_status === "string" &&
    typeof v.clarification_required === "boolean" &&
    typeof v.professional_review_recommended === "boolean" &&
    typeof v.model_id === "string" &&
    typeof v.model_revision === "string" &&
    typeof v.prompt_version === "string" &&
    typeof v.is_demo === "boolean"
  );
}

function isHttpUrl(url: string | null): url is string {
  return url !== null && /^https?:\/\//i.test(url);
}

function httpErrorMessage(status: number): string {
  if (status === 422) {
    return "That message could not be processed. Check that it is not empty or too long.";
  }
  if (status === 503) {
    return "The assistant service is unavailable right now. Please try again shortly.";
  }
  if (status === 504) {
    return "The assistant took too long to respond. Please try again.";
  }
  if (status === 502) {
    return "The assistant returned an invalid response. Please try again.";
  }
  return "Something went wrong. Please try again.";
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [failedText, setFailedText] = useState<string | null>(null);
  const nextId = useRef(1);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function submit(text: string, addUserMessage: boolean) {
    if (!text || loading) return;
    setError(null);
    setFailedText(null);
    if (addUserMessage) {
      const id = nextId.current++;
      setMessages((current) => [...current, { id, role: "user", text }]);
      setInput("");
    }
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
      });
      if (!response.ok) {
        setError(httpErrorMessage(response.status));
        setFailedText(text);
        return;
      }
      const data: unknown = await response.json();
      if (!isChatApiResponse(data)) {
        setError("The API returned an unexpected response.");
        setFailedText(text);
        return;
      }
      const id = nextId.current++;
      setMessages((current) => [...current, { id, role: "assistant", data }]);
    } catch (err) {
      if (err instanceof DOMException && err.name === "TimeoutError") {
        setError("The request timed out. Please try again.");
      } else {
        setError(`Could not reach the CuraLLM API at ${API_URL}. Is it running?`);
      }
      setFailedText(text);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submit(input.trim(), true);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void submit(input.trim(), true);
    }
  }

  return (
    <section
      aria-label="Chat"
      className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 px-4 py-6"
    >
      <div
        role="log"
        aria-label="Conversation"
        aria-live="polite"
        className="flex-1 space-y-4"
      >
        {messages.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 p-6 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-400">
            <p className="font-medium text-slate-800 dark:text-slate-200">
              Ask a general health question.
            </p>
            <p className="mt-1">
              This demo returns a fixed placeholder answer. It does not search
              medical sources yet.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {EXAMPLE_QUESTIONS.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => setInput(question)}
                  className="rounded-full border border-slate-300 px-3 py-1 text-left text-xs hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 dark:border-slate-700 dark:hover:bg-slate-800"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) =>
          message.role === "user" ? (
            <div key={message.id} className="flex justify-end">
              <p className="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-sm bg-sky-600 px-4 py-2 text-sm text-white">
                {message.text}
              </p>
            </div>
          ) : (
            <AssistantCard key={message.id} data={message.data} />
          ),
        )}

        {loading && (
          <p role="status" className="text-sm text-slate-500 dark:text-slate-400">
            Thinking…
          </p>
        )}
        <div ref={endRef} />
      </div>

      {error && (
        <div
          role="alert"
          className="flex items-start justify-between gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
        >
          <span>{error}</span>
          {failedText && (
            <button
              type="button"
              onClick={() => void submit(failedText, false)}
              disabled={loading}
              className="shrink-0 rounded-md border border-red-300 px-2 py-1 text-xs font-medium hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 dark:border-red-800 dark:hover:bg-red-900"
            >
              Retry
            </button>
          )}
        </div>
      )}

      <form onSubmit={onSubmit} className="space-y-2">
        <label htmlFor="message" className="sr-only">
          Your question
        </label>
        <textarea
          id="message"
          value={input}
          onChange={(event: ChangeEvent<HTMLTextAreaElement>) =>
            setInput(event.target.value)
          }
          onKeyDown={onKeyDown}
          maxLength={MAX_CHARS}
          rows={3}
          placeholder="Type your question. Press Enter to send, Shift+Enter for a new line."
          className="w-full resize-none rounded-xl border border-slate-300 bg-white p-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {input.length}/{MAX_CHARS}
          </span>
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-full bg-sky-600 px-5 py-2 text-sm font-medium text-white hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:focus:ring-offset-slate-950"
          >
            Send
          </button>
        </div>
      </form>
    </section>
  );
}

function AssistantCard({ data }: { data: ChatApiResponse }) {
  const citations = data.citations.filter(isCitation);
  return (
    <article className="max-w-[95%] space-y-3 rounded-2xl rounded-bl-sm border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-2">
        <span className="font-semibold">CuraLLM</span>
        {data.is_demo && (
          <span className="rounded-full border border-amber-300 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200">
            Demo response
          </span>
        )}
      </div>

      <p className="whitespace-pre-wrap break-words">{data.answer}</p>

      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Sources
        </h2>
        {citations.length === 0 ? (
          <p className="mt-1 text-slate-600 dark:text-slate-400">
            No sources. This demo does not retrieve evidence yet.
          </p>
        ) : (
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {citations.map((citation) => (
              <li key={citation.passage_id}>
                {isHttpUrl(citation.source_url) ? (
                  <a
                    href={citation.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sky-700 underline dark:text-sky-400"
                  >
                    {citation.title}
                  </a>
                ) : (
                  citation.title
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {data.professional_review_recommended && (
        <p className="rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-700 dark:bg-slate-800 dark:text-slate-300">
          This is general information, not medical advice. Consider speaking with a
          qualified clinician about your situation.
        </p>
      )}

      <details className="text-xs text-slate-600 dark:text-slate-400">
        <summary className="cursor-pointer select-none">Technical details</summary>
        <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
          <dt className="font-medium">Model</dt>
          <dd className="break-all">
            {data.model_id} ({data.model_revision})
          </dd>
          <dt className="font-medium">Prompt version</dt>
          <dd className="break-all">{data.prompt_version}</dd>
          <dt className="font-medium">Safety check</dt>
          <dd>{data.safety_status.replace(/_/g, " ")}</dd>
          <dt className="font-medium">Request ID</dt>
          <dd className="break-all">{data.request_id}</dd>
        </dl>
      </details>
    </article>
  );
}
