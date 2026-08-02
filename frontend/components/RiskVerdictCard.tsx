import type { CheckResponse, RiskBasis, RiskPoint } from "@/lib/types";

function PointRow({
  point,
  number,
  delayIndex,
  selectedBasis,
  onSelectBasis,
}: {
  point: RiskPoint;
  number: number;
  delayIndex: number;
  selectedBasis: RiskBasis | null;
  onSelectBasis: (basis: RiskBasis) => void;
}) {
  const basis = point.basis;
  const selected = basis !== null && basis === selectedBasis;

  return (
    <li
      className="animate-fade-in flex gap-3 py-4"
      style={{
        animationDelay: `${delayIndex * 0.12}s`,
        animationFillMode: "backwards",
      }}
    >
      <span
        className={`shrink-0 font-semibold transition-all font-data text-ink ${
          selected ? "text-base" : "text-sm"
        }`}
      >
        {number}
      </span>
      <div className="min-w-0 flex-1">
        <p
          className={`leading-relaxed transition-all ${
            selected ? "text-base font-medium text-ink" : "text-sm text-ink/70"
          }`}
        >
          {point.text}
        </p>
        <p
          className={`mt-1 leading-relaxed transition-all ${
            selected ? "text-[15px] text-ink/85" : "text-sm text-ink/75"
          }`}
        >
          {point.detail}
        </p>

        {basis &&
          (basis.source_key ? (
            <button
              onClick={() => onSelectBasis(basis)}
              className={`mt-1.5 block max-w-full truncate text-left underline decoration-dotted underline-offset-4 transition-all font-data ${
                selected
                  ? "text-[13px] font-medium text-brand decoration-brand/50"
                  : "text-xs text-muted decoration-line hover:text-brand"
              }`}
            >
              {selected ? "◀ " : ""}
              근거 · {basis.source}
              {basis.page ? ` ${basis.page}p` : ""}
            </button>
          ) : (
            <p className="mt-1.5 truncate text-xs text-muted font-data">
              근거 · {basis.source}
            </p>
          ))}
      </div>
    </li>
  );
}

function SectionLabel({ tone, children }: { tone: "info" | "risk"; children: React.ReactNode }) {
  return (
    <p
      className={`mt-5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.15em] font-data ${
        tone === "risk" ? "text-risk-red" : "text-brand"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${tone === "risk" ? "bg-risk-red" : "bg-brand"}`} />
      {children}
    </p>
  );
}

/** 같은 계층 검색축(상품설명서 vs 특약/기본약관)으로 나온 포인트를 "상품 정보 -> 위험 체크"
 * 두 그룹으로 나눠서 보여준다. 백엔드 호출은 한 번뿐이고, 이미 받은 응답을 순서만 나눠서
 * 단계적으로 보여주는 것 — LLM을 두 번 부르지 않고도 "설명 먼저, 위험 나중" 흐름을 낸다. */
export function RiskVerdictCard({
  report,
  selectedBasis,
  onSelectBasis,
}: {
  report: CheckResponse;
  selectedBasis: RiskBasis | null;
  onSelectBasis: (basis: RiskBasis) => void;
}) {
  const descriptionPoints = report.points.filter(
    (p) => p.type === "description",
  );
  const riskPoints = report.points.filter((p) => p.type === "risk");

  return (
    <div className="animate-fade-in">
      <div className="h-1 w-12 rounded-full bg-ink" />

      {descriptionPoints.length > 0 && (
        <>
          <SectionLabel tone="info">상품 정보</SectionLabel>
          <ol className="mt-2 divide-y divide-line border-y border-line border-l-2 border-l-brand/30 pl-3">
            {descriptionPoints.map((point, i) => (
              <PointRow
                key={i}
                point={point}
                number={i + 1}
                delayIndex={i}
                selectedBasis={selectedBasis}
                onSelectBasis={onSelectBasis}
              />
            ))}
          </ol>
        </>
      )}

      {riskPoints.length > 0 && (
        <>
          <SectionLabel tone="risk">위험 체크</SectionLabel>
          <ol className="mt-2 divide-y divide-line border-y border-line border-l-2 border-l-risk-red/40 pl-3">
            {riskPoints.map((point, i) => (
              <PointRow
                key={i}
                point={point}
                number={descriptionPoints.length + i + 1}
                delayIndex={descriptionPoints.length + i}
                selectedBasis={selectedBasis}
                onSelectBasis={onSelectBasis}
              />
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
