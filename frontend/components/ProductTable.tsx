import Link from "next/link";
import type { ProductSummary } from "@/lib/types";

const CATEGORY_STYLES: Record<string, string> = {
  적금: "bg-gold-soft text-gold",
  예금: "bg-gold-soft text-gold",
  대출: "bg-brand/10 text-brand",
};

export function ProductTable({ products }: { products: ProductSummary[] }) {
  return (
    <div className="overflow-hidden rounded-sm border border-line bg-panel">
      <div className="grid grid-cols-[5rem_1fr_8rem_10rem] gap-4 border-b border-line bg-[#F7F8FB] px-5 py-2.5 text-xs font-medium text-muted font-data">
        <span>구분</span>
        <span>상품명</span>
        <span>금리</span>
        <span className="text-right">공시일 2026.07.01</span>
      </div>
      <ul>
        {products.map((p, i) => (
          <li key={p.id} className={i !== 0 ? "border-t border-line" : ""}>
            <Link
              href={`/products/${p.id}`}
              className="grid grid-cols-[5rem_1fr_8rem_10rem] items-center gap-4 px-5 py-4 transition-colors hover:bg-[#F7F8FB]"
            >
              <span
                className={`w-fit rounded-sm px-2 py-0.5 text-xs font-medium ${
                  CATEGORY_STYLES[p.category] ?? "bg-line/60 text-muted"
                }`}
              >
                {p.category}
              </span>
              <span>
                <span className="block font-medium text-ink">{p.name}</span>
                <span className="mt-0.5 block text-sm text-muted">
                  {p.bank} · {p.description}
                </span>
              </span>
              <span className="font-data text-base font-semibold text-brand">
                {p.headline_rate}
              </span>
              <span className="text-right text-sm font-medium text-gold">
                상세보기 →
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
