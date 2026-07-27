"use client";

import { useState } from "react";
import type { CatalogProduct } from "@/lib/types";
import { SignupFlow } from "./SignupFlow";

function groupBy(products: CatalogProduct[], key: (p: CatalogProduct) => string): Map<string, CatalogProduct[]> {
  const groups = new Map<string, CatalogProduct[]>();
  for (const p of products) {
    const k = key(p);
    const list = groups.get(k) ?? [];
    list.push(p);
    groups.set(k, list);
  }
  return groups;
}

export function CatalogList({ products }: { products: CatalogProduct[] }) {
  const subCategoryGroups = groupBy(products, (p) => p.sub_category);
  const subCategories = [...subCategoryGroups.keys()];
  const [activeSub, setActiveSub] = useState(subCategories[0]);

  const banks = [...groupBy(products, (p) => p.bank).keys()];
  const [activeBank, setActiveBank] = useState<string | null>(null);

  const items = products.filter(
    (p) => p.sub_category === activeSub && (activeBank === null || p.bank === activeBank),
  );

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-b border-line pb-1">
        <div className="flex flex-wrap gap-1">
          {subCategories.map((sub) => (
            <button
              key={sub}
              onClick={() => setActiveSub(sub)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors ${
                activeSub === sub ? "border-b-2 border-brand text-brand" : "text-muted hover:text-ink"
              }`}
            >
              {sub}
              <span className="ml-1 text-xs text-muted">{subCategoryGroups.get(sub)!.length}</span>
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-1.5 pb-1.5">
          <button
            onClick={() => setActiveBank(null)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              activeBank === null ? "bg-brand/10 text-brand" : "text-muted hover:text-ink"
            }`}
          >
            전체 은행
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
            </button>
          ))}
        </div>
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
            <SignupFlow productId={p.product_id} compact />
          </li>
        ))}
      </ul>
      {items.length === 0 && (
        <p className="px-2 py-6 text-center text-sm text-muted">해당 조건의 상품이 없습니다.</p>
      )}
    </div>
  );
}
