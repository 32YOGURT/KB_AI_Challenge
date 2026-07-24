"use client";

import { useState } from "react";
import { checkProduct } from "@/lib/api";
import { useUser } from "@/context/UserContext";
import type { CheckResponse } from "@/lib/types";
import { RiskVerdictCard } from "./RiskVerdictCard";

const SCAN_STEPS = [
  "상품 기본조건 및 약관 조항 조회 중",
  "내 소비·자산 데이터와 우대조건 대조 중",
  "중도해지·페널티 리스크 판정 중",
];

type Phase = "idle" | "scanning" | "result" | "error";

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function SignupFlow({ productId }: { productId: string }) {
  const { activeUser } = useUser();
  const [phase, setPhase] = useState<Phase>("idle");
  const [report, setReport] = useState<CheckResponse | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  const startScan = async () => {
    if (!activeUser) return;
    setPhase("scanning");
    setConfirmed(false);
    try {
      const [result] = await Promise.all([
        checkProduct(productId, activeUser.id),
        delay(2200),
      ]);
      setReport(result);
      setPhase("result");
    } catch {
      setPhase("error");
    }
  };

  const close = () => {
    setPhase("idle");
    setReport(null);
  };

  return (
    <>
      <button
        onClick={startScan}
        disabled={!activeUser}
        className="w-full rounded-sm bg-gold px-6 py-3.5 text-base font-semibold text-white transition-colors hover:bg-[#8f6423] disabled:opacity-50"
      >
        가입하기
      </button>

      {phase !== "idle" && (
        <div className="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-ink/70 px-4 backdrop-blur-sm">
          {phase === "scanning" && (
            <div className="relative w-full max-w-md overflow-hidden rounded-sm border border-line bg-panel p-8">
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
                    style={{ animationDelay: `${i * 0.5}s`, animationFillMode: "backwards" }}
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-gold" />
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {phase === "result" && report && (
            <div className="w-full max-w-md">
              <RiskVerdictCard report={report} />
              <div className="mt-4 flex gap-3">
                <button
                  onClick={close}
                  className="flex-1 rounded-sm border border-line bg-panel px-4 py-3 text-sm font-semibold text-ink transition-colors hover:bg-[#F7F8FB]"
                >
                  ◀ 다시 생각하기
                </button>
                <button
                  onClick={() => setConfirmed(true)}
                  className="flex-1 rounded-sm px-4 py-3 text-sm font-medium text-white/80 underline decoration-white/30 underline-offset-4 transition-colors hover:text-white"
                >
                  위험 감수하고 가입 ➔
                </button>
              </div>
              {confirmed && (
                <p className="animate-fade-in mt-3 text-center text-xs text-white/70 font-data">
                  (데모) 가입 절차 진행 시뮬레이션 — 실제 가입은 진행되지 않았습니다.
                </p>
              )}
            </div>
          )}

          {phase === "error" && (
            <div className="w-full max-w-sm rounded-sm border border-line bg-panel p-6 text-center">
              <p className="text-sm text-ink">스캔에 실패했습니다. 백엔드 서버 상태를 확인해주세요.</p>
              <button
                onClick={close}
                className="mt-4 rounded-sm border border-line px-4 py-2 text-sm text-ink hover:bg-[#F7F8FB]"
              >
                닫기
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
