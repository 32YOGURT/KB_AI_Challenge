interface Row {
  key: string;
  bank: string;
  name: string;
  note: string;
  rate: string;
}

export function RateProductList({ rows }: { rows: Row[] }) {
  return (
    <ul className="overflow-hidden rounded-sm border border-line bg-panel">
      {rows.map((r, i) => (
        <li
          key={r.key}
          className={`grid grid-cols-[10rem_1fr_8rem] items-center gap-4 px-5 py-4 ${
            i !== 0 ? "border-t border-line" : ""
          }`}
        >
          <span className="text-sm text-muted">{r.bank}</span>
          <span>
            <span className="block font-medium text-ink">{r.name}</span>
            <span className="mt-0.5 block text-xs text-muted">{r.note}</span>
          </span>
          <span className="text-right font-data text-base font-semibold text-brand">{r.rate}</span>
        </li>
      ))}
    </ul>
  );
}
