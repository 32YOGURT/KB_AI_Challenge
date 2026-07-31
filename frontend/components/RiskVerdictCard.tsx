import type { CheckResponse, RiskBasis } from "@/lib/types";

const LEVEL_META = {
  RED: { word: "위험", text: "text-risk-red", bar: "bg-risk-red" },
  YELLOW: { word: "주의", text: "text-risk-yellow", bar: "bg-risk-yellow" },
  GREEN: { word: "안전", text: "text-risk-green", bar: "bg-risk-green" },
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
    <div className="animate-fade-in">
      <div className={`h-1 w-12 rounded-full ${meta.bar}`} />
      <div className="mt-3 flex items-baseline gap-2">
        <span className={`text-lg font-semibold ${meta.text}`}>{meta.word}</span>
        <span className="text-[11px] uppercase tracking-[0.2em] text-muted font-data">
          Fin-Guard AI 팩트체크
        </span>
      </div>

      <ol className="mt-4 divide-y divide-line border-y border-line">
        {report.points.map((point, i) => {
          const basis = point.basis;
          const selected = basis !== null && basis === selectedBasis;

          return (
            <li key={i} className="flex gap-3 py-4">
              <span
                className={`shrink-0 font-semibold transition-all font-data ${meta.text} ${
                  selected ? "text-base" : "text-sm"
                }`}
              >
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <p
                  className={`leading-relaxed transition-all ${
                    selected ? "text-base font-medium text-ink" : "text-sm text-ink/70"
                  }`}
                >
                  {point.text}
                </p>

                {basis &&
                  (basis.source_key ? (
                    <button
                      onClick={() => onSelectBasis(basis)}
                      className={`mt-1.5 block max-w-full truncate text-left underline decoration-dotted underline-offset-4 transition-all font-data ${
                        selected
                          ? "text-[13px] font-medium text-brand decoration-brand/50"
                          : "text-[11px] text-muted decoration-line hover:text-brand"
                      }`}
                    >
                      {selected ? "◀ " : ""}
                      근거 · {basis.source}
                      {basis.page ? ` ${basis.page}p` : ""}
                    </button>
                  ) : (
                    <p className="mt-1.5 truncate text-[11px] text-muted font-data">
                      근거 · {basis.source}
                    </p>
                  ))}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
