import type { CheckResponse, RiskBasis } from "@/lib/types";

const LEVEL_META = {
  RED: { word: "위험", border: "border-risk-red", badge: "border-risk-red text-risk-red", tint: "bg-risk-red-soft" },
  YELLOW: { word: "주의", border: "border-risk-yellow", badge: "border-risk-yellow text-risk-yellow", tint: "bg-risk-yellow-soft" },
  GREEN: { word: "안전", border: "border-risk-green", badge: "border-risk-green text-risk-green", tint: "bg-risk-green-soft" },
} as const;

export function RiskVerdictCard({
  report,
  selectedBasis,
  onSelectBasis,
}: {
  report: CheckResponse;
  selectedBasis: RiskBasis | null;
  onSelectBasis: (basis: RiskBasis) => void;
}) {
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

      <ol className="mt-5 space-y-4">
        {report.points.map((point, i) => (
          <li key={i} className="flex gap-3 text-sm leading-relaxed text-ink/90">
            <span
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold font-data ${meta.tint} ${meta.badge.split(" ")[1]}`}
            >
              {i + 1}
            </span>
            <div className="min-w-0">
              <p>{point.text}</p>
              {point.basis &&
                (point.basis.source_key ? (
                  <button
                    onClick={() => onSelectBasis(point.basis!)}
                    className={`mt-1.5 block w-full rounded-sm border px-2.5 py-1.5 text-left text-[11px] leading-relaxed transition-colors font-data ${
                      selectedBasis === point.basis
                        ? "border-brand/40 bg-brand/5 text-brand"
                        : "border-line text-muted hover:border-brand/30 hover:text-ink"
                    }`}
                  >
                    <span className="block truncate">
                      근거 · {point.basis.source}
                      {point.basis.page && ` ${point.basis.page}p`}
                    </span>
                    <span className="mt-0.5 block text-[10px] opacity-70">
                      {selectedBasis === point.basis ? "◀ 원문에서 보는 중" : "원문 보기 ◀"}
                    </span>
                  </button>
                ) : (
                  <p className="mt-1 text-[11px] leading-relaxed text-muted font-data">
                    근거 · {point.basis.source}
                  </p>
                ))}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
