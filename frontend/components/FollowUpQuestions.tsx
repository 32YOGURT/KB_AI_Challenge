"use client";

import { useState } from "react";
import { askQuestion } from "@/lib/api";
import type { AskResponse, RiskBasis, SuggestedQuestion } from "@/lib/types";

// 같은 질문을 다시 눌러도 LLM을 재호출하지 않게 세션에 남긴다 (CheckWorkspace의 캐시와 같은 방식).
function cacheKey(productId: string, userId: string, question: string) {
  return `finmark.ask.${productId}:${userId}:${question}`;
}

function readCache(key: string): AskResponse | null {
  try {
    const raw = window.sessionStorage.getItem(key);
    return raw ? (JSON.parse(raw) as AskResponse) : null;
  } catch {
    return null;
  }
}

type State = { status: "loading" } | { status: "done"; answer: AskResponse } | { status: "error" };

export function FollowUpQuestions({
  productId,
  userId,
  questions,
  selectedBasis,
  onSelectBasis,
}: {
  productId: string;
  userId: string;
  questions: SuggestedQuestion[];
  selectedBasis: RiskBasis | null;
  onSelectBasis: (basis: RiskBasis) => void;
}) {
  const [open, setOpen] = useState<string | null>(null);
  const [states, setStates] = useState<Record<string, State>>({});

  if (questions.length === 0) return null;

  const toggle = (q: SuggestedQuestion) => {
    if (open === q.question) {
      setOpen(null);
      return;
    }
    setOpen(q.question);
    if (states[q.question]?.status === "done") return;

    const key = cacheKey(productId, userId, q.question);
    const cached = readCache(key);
    if (cached) {
      setStates((s) => ({ ...s, [q.question]: { status: "done", answer: cached } }));
      return;
    }

    setStates((s) => ({ ...s, [q.question]: { status: "loading" } }));
    askQuestion(productId, userId, q.question, q.search_query)
      .then((answer) => {
        window.sessionStorage.setItem(key, JSON.stringify(answer));
        setStates((s) => ({ ...s, [q.question]: { status: "done", answer } }));
      })
      .catch(() => setStates((s) => ({ ...s, [q.question]: { status: "error" } })));
  };

  return (
    <div className="mt-6">
      <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.15em] text-gold font-data">
        <span className="h-1.5 w-1.5 rounded-full bg-gold" />
        더 궁금한 점
      </p>

      <ul className="mt-2 space-y-1.5">
        {questions.map((q) => {
          const state = states[q.question];
          const expanded = open === q.question;

          return (
            <li key={q.question}>
              <button
                onClick={() => toggle(q)}
                aria-expanded={expanded}
                className={`flex w-full items-start gap-2 rounded-sm border px-3 py-2 text-left text-[13px] leading-relaxed transition-colors ${
                  expanded
                    ? "border-gold/40 bg-gold-soft text-ink"
                    : "border-line text-ink/80 hover:border-gold/30 hover:bg-gold-soft/40"
                }`}
              >
                <span className="shrink-0 text-gold">Q</span>
                <span className="min-w-0 flex-1">{q.question}</span>
              </button>

              {expanded && (
                <div className="animate-fade-in px-3 py-2.5">
                  {state?.status === "loading" && (
                    <p className="text-[13px] text-muted font-data">약관에서 찾는 중…</p>
                  )}
                  {state?.status === "error" && (
                    <p className="text-[13px] text-risk-red">답변을 가져오지 못했습니다.</p>
                  )}
                  {state?.status === "done" && (
                    <>
                      <p className="text-[13px] leading-relaxed text-ink/80">
                        {state.answer.answer}
                      </p>
                      {state.answer.basis &&
                        (state.answer.basis.source_key ? (
                          <button
                            onClick={() => onSelectBasis(state.answer.basis as RiskBasis)}
                            className={`mt-1.5 block max-w-full truncate text-left underline decoration-dotted underline-offset-4 transition-all font-data ${
                              state.answer.basis === selectedBasis
                                ? "text-[13px] font-medium text-brand decoration-brand/50"
                                : "text-[11px] text-muted decoration-line hover:text-brand"
                            }`}
                          >
                            {state.answer.basis === selectedBasis ? "◀ " : ""}
                            근거 · {state.answer.basis.source}
                            {state.answer.basis.page ? ` ${state.answer.basis.page}p` : ""}
                          </button>
                        ) : (
                          <p className="mt-1.5 truncate text-[11px] text-muted font-data">
                            근거 · {state.answer.basis.source}
                          </p>
                        ))}
                    </>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
