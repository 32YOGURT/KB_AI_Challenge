import type { CheckResponse } from "@/lib/types";

const LEVEL_META = {
  RED: { word: "위험", border: "border-risk-red", badge: "border-risk-red text-risk-red", tint: "bg-risk-red-soft" },
  YELLOW: { word: "주의", border: "border-risk-yellow", badge: "border-risk-yellow text-risk-yellow", tint: "bg-risk-yellow-soft" },
  GREEN: { word: "안전", border: "border-risk-green", badge: "border-risk-green text-risk-green", tint: "bg-risk-green-soft" },
} as const;

export function RiskVerdictCard({ report }: { report: CheckResponse }) {
  const meta = LEVEL_META[report.risk_level];

  return (
    <div
      className={`animate-stamp-in relative overflow-hidden rounded-sm border-l-[6px] bg-panel p-7 shadow-xl ${meta.border}`}
    >
      <div
        className={`absolute right-6 top-6 rotate-[-6deg] rounded-full border-2 border-dashed px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] font-data ${meta.badge}`}
      >
        {meta.word}
      </div>

      <p className="pr-20 text-xs uppercase tracking-[0.2em] text-muted font-data">
        Fin-Guard AI 팩트체크
      </p>
      <h3 className="mt-2 max-w-sm pr-16 font-display text-xl font-semibold italic leading-snug text-ink">
        {report.headline}
      </h3>

      <ol className="mt-5 space-y-2.5">
        {report.summary_lines.map((line, i) => (
          <li key={i} className="flex gap-3 text-sm leading-relaxed text-ink/90">
            <span
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold font-data ${meta.tint} ${meta.badge.split(" ")[1]}`}
            >
              {i + 1}
            </span>
            <span>{line}</span>
          </li>
        ))}
      </ol>

      {report.basis.length > 0 && (
        <div className="mt-5 space-y-1.5 border-t border-line pt-3">
          {report.basis.map((b, i) => (
            <p key={i} className="text-[11px] leading-relaxed text-muted font-data">
              근거 · {b.source} — &ldquo;{b.clause}&rdquo;
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
