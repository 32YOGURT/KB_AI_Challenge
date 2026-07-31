"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { checkProduct } from "@/lib/api";
import { useUser } from "@/context/UserContext";
import type { CheckResponse, RiskBasis } from "@/lib/types";
import { RiskVerdictCard } from "./RiskVerdictCard";
import { SourcePdfViewer } from "./SourcePdfViewer";
import { UserSwitcher } from "./UserSwitcher";

const SCAN_STEPS = [
  "상품 기본조건 및 약관 조항 조회 중",
  "내 소비·자산 데이터와 우대조건 대조 중",
  "중도해지·페널티 리스크 판정 중",
];

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const ACTION_BUTTON =
  "rounded-sm border border-line px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-paper";

// 원문 PDF를 보고 돌아왔을 때 스캔(=LLM 호출)을 다시 돌리지 않도록 결과를 세션에 남긴다.
// 유저를 전환하면 키가 달라져서 새로 판정된다.
function readCache(key: string): CheckResponse | null {
  try {
    const raw = window.sessionStorage.getItem(key);
    return raw ? (JSON.parse(raw) as CheckResponse) : null;
  } catch {
    return null;
  }
}

/** 스캔/에러처럼 분할 뷰가 필요 없는 상태를 어두운 전체 화면 가운데에 띄운다. */
function Centered({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen items-center justify-center bg-[#22262c] px-6">
      <div className="w-full max-w-xl">{children}</div>
    </div>
  );
}

export function CheckWorkspace({ productId }: { productId: string }) {
  const router = useRouter();
  const { activeUser, loading } = useUser();
  const [result, setResult] = useState<{
    runId: string;
    report: CheckResponse;
  } | null>(null);
  const [errorRunId, setErrorRunId] = useState<string | null>(null);
  const [confirmedRunId, setConfirmedRunId] = useState<string | null>(null);
  const [picked, setPicked] = useState<{
    runId: string;
    basis: RiskBasis;
  } | null>(null);

  // 이미 시작한 (상품, 유저) 조합. StrictMode의 effect 재실행으로 LLM을 두 번 부르는 걸 막는다.
  const startedRef = useRef<string | null>(null);
  // 화면 상태는 runId 비교로 파생시킨다 — 유저를 전환하면 옛 결과/선택이 자동으로 무시된다.
  const runId = activeUser ? `${productId}:${activeUser.id}` : null;

  useEffect(() => {
    if (!activeUser || !runId || startedRef.current === runId) return;
    startedRef.current = runId;

    const cacheKey = `finguard.check.${runId}`;
    const cached = readCache(cacheKey);
    const load = cached
      ? Promise.resolve(cached)
      : Promise.all([checkProduct(productId, activeUser.id), delay(2200)]).then(
          ([report]) => {
            window.sessionStorage.setItem(cacheKey, JSON.stringify(report));
            return report;
          },
        );

    load
      .then((report) => setResult({ runId, report }))
      .catch(() => setErrorRunId(runId));
  }, [productId, activeUser, runId]);

  if (!loading && !activeUser) {
    return (
      <Centered>
        <div className="rounded-sm border border-line bg-panel p-6 text-center">
          <p className="text-sm text-ink">
            유저 프로필을 불러오지 못했습니다. 백엔드 서버 상태를 확인해주세요.
          </p>
        </div>
      </Centered>
    );
  }

  if (errorRunId === runId) {
    return (
      <Centered>
        <div className="rounded-sm border border-line bg-panel p-6 text-center">
          <p className="text-sm text-ink">
            스캔에 실패했습니다. 백엔드 서버 상태를 확인해주세요.
          </p>
          <button
            onClick={() => router.back()}
            className="mt-4 rounded-sm border border-line px-4 py-2 text-sm text-ink hover:bg-[#F7F8FB]"
          >
            ◀ 돌아가기
          </button>
        </div>
      </Centered>
    );
  }

  if (!result || result.runId !== runId) {
    return (
      <Centered>
        <div className="relative overflow-hidden rounded-sm border border-line bg-panel p-8">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-32 overflow-hidden opacity-70">
            <div className="animate-scan-sweep h-16 w-full bg-gradient-to-b from-transparent via-gold/25 to-transparent" />
          </div>
          <p className="text-xs uppercase tracking-[0.2em] text-brand font-data">
            Fin-Guard AI
          </p>
          <h3 className="mt-2 font-display text-xl italic text-ink">
            가입 전 위험성 스캔 중
          </h3>
          <ul className="mt-6 space-y-2.5">
            {SCAN_STEPS.map((step, i) => (
              <li
                key={step}
                className="animate-fade-in flex items-center gap-2 text-sm text-muted font-data"
                style={{
                  animationDelay: `${i * 0.5}s`,
                  animationFillMode: "backwards",
                }}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-gold" />
                {step}
              </li>
            ))}
          </ul>
        </div>
      </Centered>
    );
  }

  const report = result.report;
  // 리포트가 뜨는 순간 첫 근거를 자동으로 띄운다 — 빈 뷰어로 시작하지 않게.
  const fallbackBasis =
    report.points.find((p) => p.basis?.source_key)?.basis ?? null;
  const selectedBasis = picked?.runId === runId ? picked.basis : fallbackBasis;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#22262c]">
      {/* PDF 뷰어 느낌의 슬림 툴바 — 유저 전환은 핵심 시연이라 여기에 남긴다. */}
      <header className="flex shrink-0 items-center gap-4 px-4 py-2">
        <button
          onClick={() => router.back()}
          className="shrink-0 rounded-full px-2.5 py-1 text-sm text-white/70 transition-colors hover:bg-white/10 hover:text-white"
        >
          ◀ 나가기
        </button>
        <p className="min-w-0 flex-1 truncate text-xs text-white/40 font-data">
          {selectedBasis
            ? `${selectedBasis.source_key.split("/").pop()} · ${selectedBasis.clause}`
            : report.product_name}
        </p>
        <UserSwitcher />
      </header>

      <div className="flex min-h-0 flex-1 flex-col md:flex-row">
        <SourcePdfViewer
          key={selectedBasis?.source_key ?? "empty"}
          basis={selectedBasis}
        />

        <aside className="max-h-[45%] w-full shrink-0 overflow-y-auto bg-panel p-6 md:max-h-none md:w-[400px]">
          <p className="text-[11px] uppercase tracking-[0.2em] text-muted font-data">
            가입 전 최종 점검
          </p>
          <h1 className="mt-1 mb-5 text-xl font-semibold text-ink">
            {report.product_name}
          </h1>

          <RiskVerdictCard
            report={report}
            selectedBasis={selectedBasis}
            onSelectBasis={(basis) => runId && setPicked({ runId, basis })}
          />

          <div className="mt-6 flex flex-col gap-2">
            <button onClick={() => router.back()} className={ACTION_BUTTON}>
              ◀ 다시 생각하기
            </button>
            <button
              onClick={() => runId && setConfirmedRunId(runId)}
              className={ACTION_BUTTON}
            >
              위험 감수하고 계속하기 ➔
            </button>
          </div>
          {confirmedRunId === runId && (
            <p className="animate-fade-in mt-2 text-center text-xs text-muted font-data">
              (데모) 실제 가입은 은행 홈페이지에서 진행됩니다.
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}
