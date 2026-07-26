import Link from "next/link";

interface Row {
  key: string;
  href: string;
  bank: string;
  name: string;
  note: string;
  rate: string;
}

export function RateProductList({ rows }: { rows: Row[] }) {
  return (
    <ul className="overflow-hidden rounded-sm border border-line bg-panel">
      {rows.map((r, i) => (
        <li key={r.key} className={i !== 0 ? "border-t border-line" : ""}>
          <Link
            href={r.href}
            className="grid grid-cols-[10rem_1fr_8rem] items-center gap-4 px-5 py-4 transition-colors hover:bg-[#F7F8FB]"
          >
            <span className="text-sm text-muted">{r.bank}</span>
            <span>
              <span className="block font-medium text-ink">{r.name}</span>
              <span className="mt-0.5 block text-xs text-muted">{r.note}</span>
            </span>
            <span className="text-right font-data text-base font-semibold text-brand">{r.rate}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
