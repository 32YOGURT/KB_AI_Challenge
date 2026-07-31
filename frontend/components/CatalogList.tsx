"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@/context/UserContext";
import type { CatalogProduct } from "@/lib/types";

export function CatalogList({ products }: { products: CatalogProduct[] }) {
  const router = useRouter();
  const { activeUser } = useUser();
  const [activeBank, setActiveBank] = useState<string | null>(null);

  const banks = [...new Set(products.map((p) => p.bank))];
  const items = activeBank === null ? products : products.filter((p) => p.bank === activeBank);

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-1.5 border-b border-line pb-3">
        <button
          onClick={() => setActiveBank(null)}
          className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            activeBank === null ? "bg-brand/10 text-brand" : "text-muted hover:text-ink"
          }`}
        >
          전체 은행
          <span className="ml-1 opacity-60">{products.length}</span>
        </button>
        {banks.map((bank) => (
          <button
            key={bank}
            onClick={() => setActiveBank(bank)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              activeBank === bank ? "bg-brand/10 text-brand" : "text-muted hover:text-ink"
            }`}
          >
            {bank}
            <span className="ml-1 opacity-60">
              {products.filter((p) => p.bank === bank).length}
            </span>
          </button>
        ))}
      </div>

      <ul className="overflow-hidden rounded-sm border border-line bg-panel">
        {items.map((p, i) => (
          <li
            key={p.product_id}
            className={`flex items-center gap-4 px-5 py-4 ${i !== 0 ? "border-t border-line" : ""}`}
          >
            <a
              href={p.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="min-w-0 flex-1 hover:underline"
            >
              <span className="block font-medium text-ink">{p.name}</span>
              <span className="mt-0.5 block text-sm text-muted">{p.bank}</span>
            </a>
            <button
              onClick={() => router.push(`/check/${p.product_id}`)}
              disabled={!activeUser}
              className="shrink-0 rounded-full border border-brand/30 bg-brand/5 px-3.5 py-1.5 text-xs font-semibold text-brand transition-colors hover:bg-brand/10 disabled:opacity-50"
            >
              AI에게 물어보기
            </button>
          </li>
        ))}
      </ul>
      {items.length === 0 && (
        <p className="px-2 py-6 text-center text-sm text-muted">해당 조건의 상품이 없습니다.</p>
      )}
    </div>
  );
}
